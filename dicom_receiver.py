#!/usr/bin/env python3
"""
DICOM Receiver for Voluson E10 - Auto Sort by Patient
-----------------------------------------------------
• Nhận file DICOM từ máy siêu âm Voluson E10
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

from pynetdicom import AE, evt, AllStoragePresentationContexts
from pydicom.dataset import Dataset
from pathlib import Path
import datetime, os, re

# ==================== CẤU HÌNH ====================
AE_TITLE = "PC"               # AE Title của máy tính (phải trùng trên Voluson)
PORT = 104                    # Port DICOM mà Voluson gửi đến
BASE_DIR = Path("./received_dicoms")
BASE_DIR.mkdir(exist_ok=True)

# ==================== HÀM LÀM SẠCH TÊN ====================
def safe_filename(name: str) -> str:
    """Loại bỏ ký tự đặc biệt, chỉ giữ chữ cái, số, gạch dưới"""
    name = re.sub(r'[^A-Za-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

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

    filename = patient_folder / f"{study_date}_{study_time}.dcm"

    try:
        ds.save_as(filename, write_like_original=False)
        print(f"📥 Nhận file DICOM: {filename}")
        print(f"   👤 Bệnh nhân: {patient_name}")
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu file: {e}")

    return 0x0000  # Success

# ==================== KHỞI TẠO DICOM SERVER ====================
handlers = [(evt.EVT_C_STORE, handle_store)]

ae = AE(ae_title=AE_TITLE)
for context in AllStoragePresentationContexts:
    ae.add_supported_context(context.abstract_syntax)

print("🏥 DICOM Receiver (Auto Sort by Patient) đang khởi động...")
print(f"   AE Title : {AE_TITLE}")
print(f"   Port     : {PORT}")
print(f"   Lưu tại  : {BASE_DIR.resolve()}")
print("   Sẵn sàng nhận file từ Voluson E10...\n")

ae.start_server(('', PORT), block=True, evt_handlers=handlers)
