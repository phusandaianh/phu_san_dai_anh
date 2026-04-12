"""mwl_sync.py

Script để tạo worklist.json từ cơ sở dữ liệu `clinic.db` (SQLAlchemy via app.py's models).
Chạy file này định kỳ (cron/Task Scheduler) hoặc trực tiếp để xuất danh sách bệnh nhân có chỉ định siêu âm.

Output: worklist.json (một list các dict với các trường cần cho MWL)
"""
import json
import os
import sqlite3
import importlib.util
import sys

import mwl_store
from name_format import patient_name_title_vi

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, 'clinic.db')
WORKLIST_JSON = os.path.join(ROOT, 'worklist.json')

# Import app module (it defines db and models)
# Register module in sys.modules before exec to avoid alias issues in app.py
spec = importlib.util.spec_from_file_location('app', os.path.join(ROOT, 'app.py'))
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load app module from: {os.path.join(ROOT, 'app.py')}")
app_module = importlib.util.module_from_spec(spec)
sys.modules['app'] = app_module
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


def _rows_to_entries(rows, accession_builder):
    def row_get(row, key, default=''):
        try:
            return row[key]
        except Exception:
            return default

    entries = []
    for row in rows:
        appt_id = row_get(row, 'appt_id')
        if appt_id is None:
            continue
        appt_dt = row_get(row, 'appointment_date') or ''
        appt_date = (appt_dt[:10] or '').replace('-', '')
        appt_time = (appt_dt[11:19] or '').replace(':', '')
        if len(appt_time) == 4:
            appt_time += '00'
        if not appt_date or not appt_time:
            continue
        dob = (row_get(row, 'date_of_birth') or '').replace('-', '')
        study_desc = (row_get(row, 'study_description') or row_get(row, 'service_type') or 'Siêu âm').strip()
        expected_delivery_date = (row_get(row, 'expected_delivery_date') or '').strip()
        if expected_delivery_date and 'dks ' not in study_desc.lower():
            dks_display = expected_delivery_date
            if len(expected_delivery_date) == 10 and expected_delivery_date[4] == '-' and expected_delivery_date[7] == '-':
                dks_display = f"{expected_delivery_date[8:10]}/{expected_delivery_date[5:7]}/{expected_delivery_date[0:4]}"
            study_desc = f"{study_desc} | DKS {dks_display}"
        entries.append({
            'PatientName': patient_name_title_vi(row_get(row, 'patient_name') or ''),
            'PatientID': row_get(row, 'patient_code') or f"PAT_{appt_id}",
            'PatientBirthDate': dob,
            'StudyDescription': study_desc,
            'Modality': 'US',
            'ScheduledProcedureStepStartDate': appt_date,
            'ScheduledProcedureStepStartTime': appt_time,
            'AccessionNumber': accession_builder(row),
            'ExpectedDeliveryDate': expected_delivery_date,
        })
    return entries


def build_worklist_entries():
    """Build MWL entries from clinical_service + clinical_service_setting first, then fallback."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Nguồn chính: chỉ định cận lâm sàng (thực tế giao diện đang dùng nguồn này)
    sql_cs = """
    SELECT
      a.id AS appt_id,
      a.appointment_date,
      a.service_type,
      a.expected_delivery_date,
      p.name AS patient_name,
      p.patient_id AS patient_code,
      p.date_of_birth,
      cs.id AS clinical_service_id,
      cs.Maysieuam_accession AS clinical_service_accession,
      css.name AS study_description,
      css.service_group AS service_group
    FROM clinical_service cs
    JOIN appointment a ON a.id = cs.appointment_id
    LEFT JOIN patient p ON p.id = a.patient_id
    LEFT JOIN clinical_service_setting css ON css.id = cs.service_id
    WHERE COALESCE(a.status, 'pending') IN ('pending','scheduled')
      AND date(a.appointment_date) = date('now', 'localtime')
      AND (
        LOWER(COALESCE(css.name, '')) LIKE '%siêu âm%'
        OR LOWER(COALESCE(css.name, '')) LIKE '%sieu am%'
        OR LOWER(COALESCE(css.service_group, '')) LIKE '%siêu âm%'
        OR LOWER(COALESCE(css.service_group, '')) LIKE '%sieu am%'
      )
    ORDER BY a.appointment_date, cs.id
    """
    cs_rows = cur.execute(sql_cs).fetchall()
    entries = _rows_to_entries(
        cs_rows,
        lambda r: (r['clinical_service_accession'] or f"ACC{int(r['appt_id']):06d}-svc{int(r['clinical_service_id'])}")
    )
    # Những lịch đã có chỉ định cận lâm sàng siêu âm từ nguồn chính
    # thì không thêm fallback theo appointment nữa để tránh trùng dòng.
    appt_ids_with_cs = set()
    for r in cs_rows:
        try:
            appt_ids_with_cs.add(int(r['appt_id']))
        except Exception:
            pass

    # Fallback: lịch hẹn có service_type chứa từ khóa siêu âm
    # chỉ thêm nếu chưa có accession tương ứng
    sql_appt = """
    SELECT
      a.id AS appt_id,
      a.appointment_date,
      a.service_type,
      a.expected_delivery_date,
      p.name AS patient_name,
      p.patient_id AS patient_code,
      p.date_of_birth
    FROM appointment a
    LEFT JOIN patient p ON p.id = a.patient_id
    WHERE COALESCE(a.status, 'pending') IN ('pending','scheduled')
      AND date(a.appointment_date) = date('now', 'localtime')
    ORDER BY a.appointment_date, a.id
    """
    appt_rows = cur.execute(sql_appt).fetchall()
    conn.close()

    existing_accessions = {e['AccessionNumber'] for e in entries}
    for row in appt_rows:
        # Skip fallback nếu lịch đã có entry từ clinical_service
        try:
            if int(row['appt_id']) in appt_ids_with_cs:
                continue
        except Exception:
            pass
        if not is_ultrasound(row['service_type'] or ''):
            continue
        appt_acc = f"ACC{int(row['appt_id']):06d}"
        if appt_acc in existing_accessions:
            continue
        fallback_entries = _rows_to_entries([row], lambda _r: appt_acc)
        for e in fallback_entries:
            if e['AccessionNumber'] not in existing_accessions:
                entries.append(e)
                existing_accessions.add(e['AccessionNumber'])

    # Tránh 2 dòng cho cùng 1 lịch (ACC000123 từ fallback + ACC000123-svc từ CLS).
    return mwl_store.dedupe_mwl_entry_dicts(entries)


def write_worklist(entries):
    with open(WORKLIST_JSON, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(entries)} entries to {WORKLIST_JSON}")

def _normalize_entries(entries):
    """Normalize entries to compare logical equality across runs."""
    norm = []
    for e in entries or []:
        norm.append({
            'PatientName': e.get('PatientName') or '',
            'PatientID': e.get('PatientID') or '',
            'PatientBirthDate': e.get('PatientBirthDate') or '',
            'StudyDescription': e.get('StudyDescription') or '',
            'Modality': e.get('Modality') or '',
            'ScheduledProcedureStepStartDate': e.get('ScheduledProcedureStepStartDate') or '',
            'ScheduledProcedureStepStartTime': e.get('ScheduledProcedureStepStartTime') or '',
            'AccessionNumber': e.get('AccessionNumber') or '',
            'ExpectedDeliveryDate': e.get('ExpectedDeliveryDate') or '',
        })
    norm.sort(key=lambda x: (
        x['AccessionNumber'],
        x['ScheduledProcedureStepStartDate'],
        x['ScheduledProcedureStepStartTime'],
        x['PatientID']
    ))
    return norm


if __name__ == '__main__':
    entries = build_worklist_entries()
    # Ensure mwl DB exists
    mwl_store.init_db()
    existing = mwl_store.get_all_entries()
    if _normalize_entries(existing) == _normalize_entries(entries):
        print(f"No changes detected. Skip sync (entries={len(entries)})")
        print('Done')
        raise SystemExit(0)
    # Upsert entries into mwl.db only when changed
    mwl_store.clear_all()
    for e in entries:
        mwl_store.upsert_entry(e)
    print(f"Inserted/updated {len(entries)} entries into mwl.db")
    print('Done')
