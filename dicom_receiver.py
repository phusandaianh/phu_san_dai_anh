#!/usr/bin/env python3
"""
DICOM Receiver for ultrasound machine - Auto Sort by Patient
-----------------------------------------------------
• Nhận file DICOM từ máy siêu âm
• Tự động tạo thư mục theo tên bệnh nhân
• Tự động đổi tên file theo thời gian chụp

Ví dụ:
received_dicoms/
 ├── Nguyen_Van_A/
 │     ├── 20251028_151147.dcm
 │     └── 20251028_151152.dcm
 └── Le_Thi_B/
       └── 20251028_152010.dcm
"""

from pynetdicom import AE, evt, AllStoragePresentationContexts, VerificationPresentationContexts
from pydicom.dataset import Dataset
from pathlib import Path
import datetime, os, re
import json
import urllib.request
import urllib.error

# ==================== CẤU HÌNH ====================
AE_TITLE = "PC"               # AE Title của máy tính (phải trùng trên máy siêu âm)
PORT = 11112                  # Port DICOM C-STORE từ máy siêu âm (tách riêng với MWL 104)
BASE_DIR = Path("./received_dicoms")
BASE_DIR.mkdir(exist_ok=True)
AUTOFILL_API_URL = os.environ.get("AUTOFILL_API_URL", "http://127.0.0.1:5000/api/pacs/autofill-ultrasound")
AUTOFILL_TIMEOUT_SEC = float(os.environ.get("AUTOFILL_TIMEOUT_SEC", "2.5"))

# ==================== HÀM LÀM SẠCH TÊN ====================
def safe_filename(name: str) -> str:
    """Loại bỏ ký tự đặc biệt, chỉ giữ chữ cái, số, gạch dưới"""
    name = re.sub(r'[^A-Za-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

def trigger_autofill(patient_folder_name: str, filename: str, accession_number: str = "", source_ae: str = ""):
    """Best-effort callback to Flask API for PACS autofill."""
    payload = {
        "patient_name": patient_folder_name,
        "filename": filename,
        "accession_number": accession_number or "",
        "source_ae": source_ae or ""
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        AUTOFILL_API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=AUTOFILL_TIMEOUT_SEC) as resp:
            resp_body = resp.read().decode("utf-8", errors="ignore")
            print(f"🤖 Autofill status={resp.status}: {resp_body[:300]}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        print(f"⚠️ Autofill HTTP error: {e.code} - {detail[:300]}")
    except Exception as e:
        print(f"⚠️ Autofill request failed: {e}")

# ==================== HÀM XỬ LÝ NHẬN FILE ====================
def handle_store(event):
    ds = event.dataset
    ds.file_meta = event.file_meta

    # Lấy thông tin bệnh nhân và thời gian
    patient_name = str(ds.get("PatientName", "UNKNOWN"))
    study_date = ds.get("StudyDate", datetime.datetime.now().strftime("%Y%m%d"))
    study_time = datetime.datetime.now().strftime("%H%M%S")

    # Tên thư mục và file
    safe_name = safe_filename(patient_name) or "UNKNOWN"
    patient_folder = BASE_DIR / safe_name
    patient_folder.mkdir(exist_ok=True)

    file_name_only = f"{study_date}_{study_time}.dcm"
    filename = patient_folder / file_name_only

    try:
        ds.save_as(filename, write_like_original=False)
        print(f"📥 Nhận file DICOM: {filename}")
        print(f"   👤 Bệnh nhân: {patient_name}")
        accession_number = str(ds.get("AccessionNumber", "") or "").strip()
        source_ae = ""
        try:
            source_ae = str(event.assoc.requestor.ae_title or "").strip()
        except Exception:
            source_ae = ""
        trigger_autofill(
            patient_folder_name=safe_name,
            filename=file_name_only,
            accession_number=accession_number,
            source_ae=source_ae
        )
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu file: {e}")

    return 0x0000  # Success

def handle_echo(event):
    """Trả lời C-ECHO để máy siêu âm Verify: OK."""
    try:
        source_ae = str(event.assoc.requestor.ae_title or "").strip()
    except Exception:
        source_ae = ""
    print(f"🔎 C-ECHO từ AE: {source_ae or 'UNKNOWN'} -> 0x0000")
    return 0x0000

# ==================== KHỞI TẠO DICOM SERVER ====================
handlers = [
    (evt.EVT_C_STORE, handle_store),
    (evt.EVT_C_ECHO, handle_echo),
]

ae = AE(ae_title=AE_TITLE)
for context in AllStoragePresentationContexts:
    ae.add_supported_context(context.abstract_syntax)
for context in VerificationPresentationContexts:
    ae.add_supported_context(context.abstract_syntax)

print("🏥 DICOM Receiver (Auto Sort by Patient) đang khởi động...")
print(f"   AE Title : {AE_TITLE}")
print(f"   Port     : {PORT}")
print(f"   Lưu tại  : {BASE_DIR.resolve()}")
print("   Sẵn sàng nhận file từ máy siêu âm...\n")

ae.start_server(('', PORT), block=True, evt_handlers=handlers)
