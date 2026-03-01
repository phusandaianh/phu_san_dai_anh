"""mwl_sync.py

Script để tạo worklist.json từ cơ sở dữ liệu `clinic.db` (SQLAlchemy via app.py's models).
Chạy file này định kỳ (cron/Task Scheduler) hoặc trực tiếp để xuất danh sách bệnh nhân có chỉ định siêu âm.

Output: worklist.json (một list các dict với các trường cần cho MWL)
"""
import json
import os
from datetime import datetime
import mwl_store

# Nếu bạn muốn re-use models từ app.py, import app và db
# Để tránh side-effects, chúng ta sẽ import app.py nhưng không chạy server
import importlib
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'clinic.db')
WORKLIST_JSON = os.path.join(ROOT, 'worklist.json')

# Import app module (it defines db and models)
spec = importlib.util.spec_from_file_location('app_module', os.path.join(ROOT, 'app.py'))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Get db and models
db = getattr(app_module, 'db')
Appointment = getattr(app_module, 'Appointment')
Patient = getattr(app_module, 'Patient')

# Define which service types count as ultrasound
ULTRASOUND_SERVICE_KEYWORDS = ['siêu âm', 'sieu am', 'ultrasound', 'US', 'siêu âm thai', 'siêu âm 5d']


def is_ultrasound(service_type: str) -> bool:
    if not service_type:
        return False
    s = service_type.lower()
    for kw in ULTRASOUND_SERVICE_KEYWORDS:
        if kw in s:
            return True
    return False


def build_worklist_entries():
    """Query appointments with ultrasound service and build worklist entries."""
    entries = []
    with app_module.app.app_context():
        # Query appointments with status pending or scheduled
        appts = db.session.query(Appointment).filter(Appointment.status.in_(['pending','scheduled'])).all()
        for a in appts:
            if is_ultrasound(a.service_type):
                patient = db.session.get(Patient, a.patient_id)
                entry = {
                    'PatientName': patient.name if patient else None,
                    'PatientID': patient.patient_id if patient else None,
                    'PatientBirthDate': patient.date_of_birth.strftime('%Y%m%d') if getattr(patient, 'date_of_birth', None) else None,
                    'StudyDescription': a.service_type,
                    'Modality': 'US',
                    'ScheduledProcedureStepStartDate': a.appointment_date.strftime('%Y%m%d') if a.appointment_date else None,
                    'ScheduledProcedureStepStartTime': a.appointment_date.strftime('%H%M%S') if a.appointment_date else None,
                    'AccessionNumber': f"ACC{a.id:06d}",
                }
                entries.append(entry)
    return entries


def write_worklist(entries):
    with open(WORKLIST_JSON, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} entries to {WORKLIST_JSON}")


if __name__ == '__main__':
    entries = build_worklist_entries()
    # Ensure mwl DB exists
    mwl_store.init_db()
    # Upsert entries into mwl.db
    mwl_store.clear_all()
    for e in entries:
        mwl_store.upsert_entry(e)
    print(f"Inserted/updated {len(entries)} entries into mwl.db")
    print('Done')
