import logging
import os
import time
import threading
import subprocess
import json
import sys
from datetime import datetime, timedelta
from pydicom.dataset import Dataset
from name_format import strip_accents_for_dicom_modality
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind, VerificationSOPClass


def _load_runtime_config():
    """Load MWL runtime config from voluson_config.json (best-effort)."""
    cfg = {
        'mwl_server_ae_title': 'CLINIC_SYSTEM',
        'mwl_server_port': 104,
        'mwl_server_ip': '10.17.2.2',
        'modality_station_ae_title': 'MAY_SIEU_AM',
        'modality_station_name': 'US1',
        'require_called_aet': False,
        'allowed_calling_ae_titles': [],
    }
    try:
        user_cfg = None
        if os.path.exists('voluson_config.json'):
            with open('voluson_config.json', 'r', encoding='utf-8') as f:
                user_cfg = json.load(f) or {}
        elif os.path.exists('Maysieuam_config.json'):
            # legacy name (best-effort)
            with open('Maysieuam_config.json', 'r', encoding='utf-8') as f:
                user_cfg = json.load(f) or {}
        if user_cfg is None:
            user_cfg = {}
        for k in list(cfg.keys()):
            if k in user_cfg and user_cfg[k] not in (None, ''):
                cfg[k] = user_cfg[k]
    except Exception as e:
        print(f"Could not load MWL server config: {e}")
    return cfg


_CFG = _load_runtime_config()

# Ensure stdout/stderr can write safely in Windows service/task contexts
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _safe_print(msg: str) -> None:
    """Avoid UnicodeEncodeError on Windows consoles (cp1252) when logs contain Vietnamese."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            if getattr(sys.stdout, "buffer", None):
                sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
                sys.stdout.buffer.flush()
            else:
                print(msg.encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass


# Cấu hình MWL server (SCP)
MWL_AE_TITLE = str(_CFG.get('mwl_server_ae_title', 'CLINIC_SYSTEM')).encode('ascii', errors='ignore') or b'CLINIC_SYSTEM'
MWL_PORT = int(_CFG.get('mwl_server_port', 104) or 104)
SERVER_IP = str(_CFG.get('mwl_server_ip', '10.17.2.2') or '10.17.2.2')

# Station/Modality info returned in MWL entries
STATION_AE_TITLE = str(_CFG.get('modality_station_ae_title', 'MAY_SIEU_AM')).encode('ascii', errors='ignore') or b'MAY_SIEU_AM'
STATION_NAME = str(_CFG.get('modality_station_name', 'US1') or 'US1')

# Danh sách worklist entries (cache; C-FIND luôn reload từ mwl.db trước mỗi truy vấn)
worklist_entries = []
_worklist_entries_lock = threading.Lock()
WORKLIST_JSON = 'worklist.json'
MWL_RELOAD_SIGNAL = 'mwl_reload.signal'


def load_worklist_from_db():
    """Load worklist entries from mwl_store (mwl.db) and convert to pydicom Dataset objects."""
    try:
        import mwl_store
        from pydicom.dataset import Dataset
        entries = []
        rows = mwl_store.get_all_entries()
        for item in rows:
            ds = Dataset()
            ds.PatientName = item.get('PatientName')
            ds.PatientID = item.get('PatientID')
            ds.PatientBirthDate = item.get('PatientBirthDate')
            ds.StudyDescription = item.get('StudyDescription')
            ds.Modality = item.get('Modality')
            ds.ScheduledProcedureStepStartDate = item.get('ScheduledProcedureStepStartDate')
            ds.ScheduledProcedureStepStartTime = item.get('ScheduledProcedureStepStartTime')
            ds.AccessionNumber = item.get('AccessionNumber')
            expected_delivery_date = (item.get('ExpectedDeliveryDate') or '').strip()
            if expected_delivery_date:
                # Compatibility mode: populate multiple common text fields so
                # different modalities can pick at least one for UI display.
                base_desc = (item.get('StudyDescription') or 'Sieu am')
                edd_text = f"EDD {expected_delivery_date}"
                merged_desc = base_desc if edd_text.lower() in base_desc.lower() else f"{base_desc} | {edd_text}"
                ds.StudyDescription = merged_desc
                ds.RequestedProcedureDescription = merged_desc
                ds.RequestedProcedureComments = edd_text
                ds.AdmittingDiagnosesDescription = merged_desc
                # OB-compatible field: derive LMP from EDD (~280 days)
                try:
                    edd = datetime.strptime(expected_delivery_date[:10], '%Y-%m-%d').date()
                    lmp = edd - timedelta(days=280)
                    ds.LastMenstrualDate = lmp.strftime('%Y%m%d')
                except Exception:
                    pass
            entries.append(ds)
        return entries
    except Exception as e:
        print(f"Failed to load entries from mwl_store: {e}")
        return []


def reload_worklist_from_db_now():
    """Nạp lại worklist từ mwl.db vào RAM (dùng ngay sau sync hoặc trước C-FIND)."""
    global worklist_entries
    entries = load_worklist_from_db()
    with _worklist_entries_lock:
        worklist_entries = entries
    return len(entries)


def _maybe_reload_from_signal():
    """Reload ngay khi app ghi file tín hiệu sau lưu lịch."""
    try:
        if os.path.exists(MWL_RELOAD_SIGNAL):
            reload_worklist_from_db_now()
            try:
                os.remove(MWL_RELOAD_SIGNAL)
            except Exception:
                pass
    except Exception:
        pass


def start_worklist_watcher(interval=10):
    """Start a background thread to reload worklist.json periodically."""
    def watcher():
        global worklist_entries
        last_mtime = None
        pending_mwl_reload_at = None
        pending_mwl_mtime = None
        pending_json_reload_at = None
        pending_json_mtime = None
        while True:
            try:
                _maybe_reload_from_signal()
                # Prefer loading from DB (mwl.db) if available
                if os.path.exists('mwl.db'):
                    mtime = os.path.getmtime('mwl.db')
                    now_ts = time.time()
                    if last_mtime is None:
                        # first load immediately
                        n = reload_worklist_from_db_now()
                        _safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {n} worklist entries from {os.path.abspath('mwl.db')}")
                        last_mtime = mtime
                        pending_mwl_reload_at = None
                        pending_mwl_mtime = None
                    elif mtime != last_mtime:
                        # debounce: wait a bit for sync process to finish writing all rows
                        pending_mwl_reload_at = now_ts + 1.2
                        pending_mwl_mtime = mtime
                    elif pending_mwl_reload_at and now_ts >= pending_mwl_reload_at:
                        # only reload when mtime remains stable at pending value
                        current_mtime = os.path.getmtime('mwl.db')
                        if pending_mwl_mtime is None or current_mtime == pending_mwl_mtime:
                            n = reload_worklist_from_db_now()
                            _safe_print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {n} worklist entries from {os.path.abspath('mwl.db')}")
                            last_mtime = current_mtime
                            pending_mwl_reload_at = None
                            pending_mwl_mtime = None
                        else:
                            pending_mwl_reload_at = time.time() + 1.2
                            pending_mwl_mtime = current_mtime
                else:
                    # fallback to JSON if present
                    if os.path.exists(WORKLIST_JSON):
                        mtime = os.path.getmtime(WORKLIST_JSON)
                        now_ts = time.time()
                        if last_mtime is None:
                            # load json entries immediately on first run
                            import json
                            data = []
                            try:
                                with open(WORKLIST_JSON, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                            except Exception:
                                data = []
                            tmp = []
                            from pydicom.dataset import Dataset
                            for item in data:
                                ds = Dataset()
                                ds.PatientName = item.get('PatientName')
                                ds.PatientID = item.get('PatientID')
                                ds.PatientBirthDate = item.get('PatientBirthDate')
                                ds.StudyDescription = item.get('StudyDescription')
                                ds.Modality = item.get('Modality')
                                ds.ScheduledProcedureStepStartDate = item.get('ScheduledProcedureStepStartDate')
                                ds.ScheduledProcedureStepStartTime = item.get('ScheduledProcedureStepStartTime')
                                ds.AccessionNumber = item.get('AccessionNumber')
                                tmp.append(ds)
                            worklist_entries = tmp
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {len(worklist_entries)} worklist entries from {WORKLIST_JSON}")
                            last_mtime = mtime
                            pending_json_reload_at = None
                            pending_json_mtime = None
                        elif mtime != last_mtime:
                            pending_json_reload_at = now_ts + 1.2
                            pending_json_mtime = mtime
                        elif pending_json_reload_at and now_ts >= pending_json_reload_at:
                            current_mtime = os.path.getmtime(WORKLIST_JSON)
                            if pending_json_mtime is None or current_mtime == pending_json_mtime:
                                import json
                                data = []
                                try:
                                    with open(WORKLIST_JSON, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                except Exception:
                                    data = []
                                tmp = []
                                from pydicom.dataset import Dataset
                                for item in data:
                                    ds = Dataset()
                                    ds.PatientName = item.get('PatientName')
                                    ds.PatientID = item.get('PatientID')
                                    ds.PatientBirthDate = item.get('PatientBirthDate')
                                    ds.StudyDescription = item.get('StudyDescription')
                                    ds.Modality = item.get('Modality')
                                    ds.ScheduledProcedureStepStartDate = item.get('ScheduledProcedureStepStartDate')
                                    ds.ScheduledProcedureStepStartTime = item.get('ScheduledProcedureStepStartTime')
                                    ds.AccessionNumber = item.get('AccessionNumber')
                                    tmp.append(ds)
                                worklist_entries = tmp
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {len(worklist_entries)} worklist entries from {WORKLIST_JSON}")
                                last_mtime = current_mtime
                                pending_json_reload_at = None
                                pending_json_mtime = None
                            else:
                                pending_json_reload_at = time.time() + 1.2
                                pending_json_mtime = current_mtime
                # Chỉ fallback rỗng khi dùng JSON mode và file JSON không tồn tại.
                # Nếu đang dùng mwl.db thì không được xóa danh sách vừa load từ DB.
                if (not os.path.exists('mwl.db')) and (not os.path.exists(WORKLIST_JSON)) and worklist_entries:
                    worklist_entries = []
                time.sleep(interval)
            except Exception as e:
                print(f"Worklist watcher error: {e}")
                time.sleep(interval)

    t = threading.Thread(target=watcher, daemon=True)
    t.start()

def start_auto_sync_scheduler(interval_minutes=3):
    """Tự động đồng bộ worklist từ clinic.db mỗi N phút"""
    def sync_scheduler():
        last_clinic_mtime = None
        while True:
            try:
                time.sleep(interval_minutes * 60)
                clinic_db = 'clinic.db'
                if os.path.exists(clinic_db):
                    current_mtime = os.path.getmtime(clinic_db)
                    if last_clinic_mtime is not None and current_mtime == last_clinic_mtime:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No clinic.db change -> skip auto-sync")
                        continue
                    last_clinic_mtime = current_mtime
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-syncing worklist from clinic.db...")
                result = subprocess.run(['python', 'mwl_sync.py'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    n = reload_worklist_from_db_now()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-sync completed successfully (MWL entries in RAM: {n})")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-sync failed: {result.stderr}")
            except Exception as e:
                print(f"Auto-sync error: {e}")
    
    t = threading.Thread(target=sync_scheduler, daemon=True)
    t.start()
    print(f"Started auto-sync scheduler (every {interval_minutes} minutes)")

def handle_find(event):
    """Xử lý C-FIND request"""
    reload_worklist_from_db_now()
    ds = event.identifier
    remote_ae = event.assoc.remote['ae_title']
    
    _safe_print(f"Received C-FIND request from {remote_ae}:")
    _safe_print(f"Query dataset: {ds}")
    
    req_modality = ''
    req_date = ''
    try:
        spsq = getattr(ds, 'ScheduledProcedureStepSequence', None)
        if spsq and len(spsq) > 0:
            req_modality = str(getattr(spsq[0], 'Modality', '') or '').strip().upper()
            req_date = str(getattr(spsq[0], 'ScheduledProcedureStepStartDate', '') or '').strip()
    except Exception:
        pass

    def _norm_dicom_date(value: str) -> str:
        d = (value or '').strip().replace('-', '')
        return d[:8] if len(d) >= 8 else d

    def _is_yyyymmdd(value: str) -> bool:
        return len(value) == 8 and value.isdigit()

    def _date_match(entry_date: str, query_date: str) -> bool:
        q_raw = (query_date or '').strip()
        if not q_raw:
            return True
        # Nhiều modality gửi wildcard thay vì để trống → trước đây so sánh sai → 0 kết quả
        if q_raw in ('*', '-', '?'):
            return True
        e = _norm_dicom_date(entry_date)
        if not _is_yyyymmdd(e):
            # Ca không có ngày hợp lệ 8 số: không lọc theo ngày (tránh mất worklist)
            return True
        # DICOM MWL date range: exactly YYYYMMDD-YYYYMMDD
        if len(q_raw) == 17 and q_raw[8] == '-':
            start_n, end_n = q_raw[:8], q_raw[9:17]
            if start_n.isdigit() and end_n.isdigit():
                if e < start_n:
                    return False
                if e > end_n:
                    return False
                return True
        qn = _norm_dicom_date(q_raw)
        if not _is_yyyymmdd(qn):
            return True
        return e == qn

    # Trả đúng cấu trúc MWL với ScheduledProcedureStepSequence
    with _worklist_entries_lock:
        entries_snapshot = list(worklist_entries)
    for entry in entries_snapshot:
        try:
            entry_modality = str(getattr(entry, 'Modality', 'US') or 'US').strip().upper()
            entry_date = str(getattr(entry, 'ScheduledProcedureStepStartDate', '') or '').strip()
            if req_modality and entry_modality and req_modality != entry_modality:
                continue
            if not _date_match(entry_date, req_date):
                continue

            study_desc = getattr(entry, 'StudyDescription', '') or 'Sieu am'
            study_desc = strip_accents_for_dicom_modality(study_desc)
            patient_pn = strip_accents_for_dicom_modality(getattr(entry, 'PatientName', '') or '')

            rsp = Dataset()
            # Không gửi ISO_IR 192: nhiều máy siêu âm hiển thị sai ô vuông với UTF-8 trong PN.
            # Toàn bộ chuỗi chữ ở đây đã ASCII (không dấu) để tương thích mặc định DICOM.
            rsp.QueryRetrieveLevel = 'PATIENT'
            rsp.PatientName = patient_pn
            rsp.PatientID = getattr(entry, 'PatientID', '') or ''
            rsp.PatientBirthDate = getattr(entry, 'PatientBirthDate', '') or ''
            rsp.AccessionNumber = getattr(entry, 'AccessionNumber', '') or ''
            rsp.RequestedProcedureDescription = study_desc
            # Dự kiến sinh (EDD): load_worklist_from_db đã gắn LMP = EDD-280 ngày + comment "EDD yyyy-mm-dd"
            lmp = getattr(entry, 'LastMenstrualDate', None)
            if lmp:
                rsp.LastMenstrualDate = lmp
            rpc = getattr(entry, 'RequestedProcedureComments', None)
            if rpc:
                rsp.RequestedProcedureComments = strip_accents_for_dicom_modality(str(rpc))

            sps = Dataset()
            sps.Modality = entry_modality or 'US'
            sps.ScheduledStationAETitle = STATION_AE_TITLE
            sps.ScheduledStationName = STATION_NAME
            sps.ScheduledProcedureStepStartDate = entry_date
            sps.ScheduledProcedureStepStartTime = str(getattr(entry, 'ScheduledProcedureStepStartTime', '') or '').strip()
            sps.ScheduledProcedureStepDescription = study_desc
            sps.ScheduledProcedureStepID = str(getattr(entry, 'AccessionNumber', '') or '')
            rsp.ScheduledProcedureStepSequence = [sps]

            yield (0xFF00, rsp)
        except Exception as e:
            _safe_print(f"Skip invalid MWL entry: {e}")
    
    # Báo success khi hoàn tất
    yield (0x0000, None)

def handle_echo(_event):
    """Handle C-ECHO (DICOM Verification) requests."""
    return 0x0000

def main():
    # Enable debug logging for pynetdicom
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pynetdicom').setLevel(logging.DEBUG)

    # Khởi tạo Application Entity
    ae = AE(ae_title=MWL_AE_TITLE)
    
    # Thêm presentation context cho Modality Worklist + Verification (C-ECHO)
    ae.add_supported_context(ModalityWorklistInformationFind)
    ae.add_supported_context(VerificationSOPClass)
    
    # Cấu hình chấp nhận kết nối từ máy siêu âm
    allowed_calling = _CFG.get('allowed_calling_ae_titles', [])
    if isinstance(allowed_calling, str):
        allowed_calling = [x.strip() for x in allowed_calling.split(',') if x.strip()]
    ae.require_calling_aet = [x.encode('ascii', errors='ignore') for x in allowed_calling if x] if allowed_calling else []
    ae.require_called_aet = bool(_CFG.get('require_called_aet', False))
    
    # Support all common transfer syntaxes
    for cx in ae.supported_contexts:
        cx.transfer_syntax = ['1.2.840.10008.1.2']  # Chỉ dùng Implicit VR Little Endian
    
    # Bind các handlers cho các events
    handlers = [
        (evt.EVT_C_FIND, handle_find),
        (evt.EVT_C_ECHO, handle_echo),
    ]
    
    # Thêm handler cho association events để debug
    def handle_assoc(event):
        _safe_print(f"New association from {event.assoc.remote['ae_title']}")
        return 0x0000  # Success
        
    handlers.append((evt.EVT_ACCEPTED, handle_assoc))
    
    # Start background watcher to reload worklist.json
    start_worklist_watcher(interval=5)
    
    # Start auto-sync scheduler (every 3 minutes)
    start_auto_sync_scheduler(interval_minutes=3)

    # Khởi động server
    _safe_print(f"MWL process cwd: {os.getcwd()}")
    _safe_print(f"mwl.db resolved path: {os.path.abspath('mwl.db')} (exists={os.path.exists('mwl.db')})")
    print(f"Starting Modality Worklist SCP on 0.0.0.0:{MWL_PORT}")
    ae.start_server(("0.0.0.0", MWL_PORT), block=True, evt_handlers=handlers)

    # Note: ping modality host removed (Windows compatibility + modality may vary)

if __name__ == "__main__":
    main()
