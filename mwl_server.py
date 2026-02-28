import logging
import os
import time
import threading
import subprocess
from datetime import datetime
from pydicom.dataset import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind

# Cấu hình MWL server như trong máy siêu âm (CLINIC_PC)
MWL_AE_TITLE = b'CLINIC_SYSTEM'
MWL_PORT = 104
SERVER_IP = '10.17.2.2'  # IP của server này phải là 10.17.2.2

# Cấu hình máy siêu âm Voluson
VOLUSON_HOST = '10.17.2.1'
VOLUSON_PORT = 104
VOLUSON_AE_TITLE = b'VOLUSON_E10'

# Danh sách worklist entries
worklist_entries = []
WORKLIST_JSON = 'worklist.json'


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
            entries.append(ds)
        return entries
    except Exception as e:
        print(f"Failed to load entries from mwl_store: {e}")
        return []


def start_worklist_watcher(interval=10):
    """Start a background thread to reload worklist.json periodically."""
    def watcher():
        global worklist_entries
        last_mtime = None
        while True:
            try:
                # Prefer loading from DB (mwl.db) if available
                if os.path.exists('mwl.db'):
                    mtime = os.path.getmtime('mwl.db')
                    if last_mtime is None or mtime != last_mtime:
                        worklist_entries = load_worklist_from_db()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loaded {len(worklist_entries)} worklist entries from mwl.db")
                        last_mtime = mtime
                else:
                    # fallback to JSON if present
                    if os.path.exists(WORKLIST_JSON):
                        mtime = os.path.getmtime(WORKLIST_JSON)
                        if last_mtime is None or mtime != last_mtime:
                            # load json entries
                            import json
                            data = []
                            try:
                                with open(WORKLIST_JSON, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                            except Exception:
                                data = []
                            # convert
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
                # Ensure empty list if no file
                if not os.path.exists(WORKLIST_JSON) and worklist_entries:
                    worklist_entries = []
                time.sleep(interval)
            except Exception as e:
                print(f"Worklist watcher error: {e}")
                time.sleep(interval)

    t = threading.Thread(target=watcher, daemon=True)
    t.start()

def start_auto_sync_scheduler(interval_minutes=5):
    """Tự động đồng bộ worklist từ clinic.db mỗi N phút"""
    def sync_scheduler():
        while True:
            try:
                time.sleep(interval_minutes * 60)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-syncing worklist from clinic.db...")
                result = subprocess.run(['python', 'mwl_sync.py'], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Auto-sync completed successfully")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Auto-sync failed: {result.stderr}")
            except Exception as e:
                print(f"Auto-sync error: {e}")
    
    t = threading.Thread(target=sync_scheduler, daemon=True)
    t.start()
    print(f"Started auto-sync scheduler (every {interval_minutes} minutes)")

def handle_find(event):
    """Xử lý C-FIND request"""
    ds = event.identifier
    remote_ae = event.assoc.remote['ae_title']
    
    # In thông tin request để debug
    print(f"Nhận được C-FIND request từ {remote_ae}:")
    print(f"Query dataset: {ds}")
    
    # Thêm các trường bắt buộc cho Worklist entry theo chuẩn DICOM
    for entry in worklist_entries:
        # Patient Level
        entry.SpecificCharacterSet = 'ISO_IR 192'
        entry.QueryRetrieveLevel = 'PATIENT'
        if not hasattr(entry, 'PatientName'):
            entry.PatientName = ''
        if not hasattr(entry, 'PatientID'):
            entry.PatientID = ''
            
        # Study Level
        if not hasattr(entry, 'StudyInstanceUID'):
            entry.StudyInstanceUID = '1.2.3'  # Dummy UID
        if not hasattr(entry, 'StudyID'):
            entry.StudyID = '1'
        
        # Procedure Level    
        entry.Modality = 'US'
        entry.ScheduledStationAETitle = b'VOLUSON_E10'
        entry.ScheduledStationName = 'US1'
        entry.ScheduledProcedureStepStartDate = getattr(entry, 'ScheduledProcedureStepStartDate', '')
        entry.ScheduledProcedureStepStartTime = getattr(entry, 'ScheduledProcedureStepStartTime', '')
        
        yield (0xFF00, entry)
    
    # Báo success khi hoàn tất
    yield (0x0000, None)

def main():
    # Enable debug logging for pynetdicom
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('pynetdicom').setLevel(logging.DEBUG)

    # Khởi tạo Application Entity
    ae = AE(ae_title=MWL_AE_TITLE)
    
    # Thêm presentation context cho Modality Worklist
    ae.add_supported_context(ModalityWorklistInformationFind)
    
    # Cấu hình chấp nhận kết nối từ Voluson
    ae.require_calling_aet = []  # Empty list = chấp nhận mọi AE title
    ae.require_called_aet = False  # Chấp nhận mọi Called AE title
    
    # Support all common transfer syntaxes
    for cx in ae.supported_contexts:
        cx.transfer_syntax = ['1.2.840.10008.1.2']  # Chỉ dùng Implicit VR Little Endian
    
    # Bind các handlers cho các events
    handlers = [(evt.EVT_C_FIND, handle_find)]
    
    # Thêm handler cho association events để debug
    def handle_assoc(event):
        print(f"New association from {event.assoc.remote['ae_title']}")
        return 0x0000  # Success
        
    handlers.append((evt.EVT_ACCEPTED, handle_assoc))
    
    # Start background watcher to reload worklist.json
    start_worklist_watcher(interval=5)
    
    # Start auto-sync scheduler (every 5 minutes)
    start_auto_sync_scheduler(interval_minutes=5)

    # Khởi động server
    print(f"Starting Modality Worklist SCP on 0.0.0.0:{MWL_PORT}")
    ae.start_server(("0.0.0.0", MWL_PORT), block=True, evt_handlers=handlers)

    # Thực hiện ping đến máy Voluson để kiểm tra kết nối
    os.system("ping -c 4 " + VOLUSON_HOST)

if __name__ == "__main__":
    main()
