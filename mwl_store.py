"""mwl_store.py

Simple SQLite-backed store for Modality Worklist entries using SQLAlchemy (standalone, not Flask).
Provides basic CRUD and upsert helpers used by mwl_sync.py and mwl_server.py.
"""
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import re

DB_FILENAME = 'mwl.db'
DB_URL = f'sqlite:///{DB_FILENAME}'

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()


class WorklistEntry(Base):
    __tablename__ = 'worklist_entries'
    id = Column(Integer, primary_key=True)
    patient_name = Column(String)
    patient_id = Column(String)
    patient_birthdate = Column(String)
    study_description = Column(String)
    modality = Column(String)
    scheduled_date = Column(String)
    scheduled_time = Column(String)
    accession_number = Column(String, unique=True)
    expected_delivery_date = Column(String)

    def to_dict(self):
        return {
            'id': self.id,
            'PatientName': self.patient_name,
            'PatientID': self.patient_id,
            'PatientBirthDate': self.patient_birthdate,
            'StudyDescription': self.study_description,
            'Modality': self.modality,
            'ScheduledProcedureStepStartDate': self.scheduled_date,
            'ScheduledProcedureStepStartTime': self.scheduled_time,
            'AccessionNumber': self.accession_number,
            'ExpectedDeliveryDate': self.expected_delivery_date,
        }


def init_db():
    Base.metadata.create_all(engine)
    # Backward-compatible migration for old mwl.db files.
    s = Session()
    try:
        cols = [row[1] for row in s.execute(text("PRAGMA table_info(worklist_entries)")).fetchall()]
        if 'expected_delivery_date' not in cols:
            s.execute(text("ALTER TABLE worklist_entries ADD COLUMN expected_delivery_date VARCHAR"))
            s.commit()
    finally:
        s.close()


def get_all_entries():
    s = Session()
    try:
        rows = s.query(WorklistEntry).order_by(WorklistEntry.id).all()
        return [r.to_dict() for r in rows]
    finally:
        s.close()


def upsert_entry(entry: dict):
    """Insert or update based on accession_number"""
    s = Session()
    try:
        acc = entry.get('AccessionNumber')
        row = None
        if acc:
            row = s.query(WorklistEntry).filter_by(accession_number=acc).first()
        if not row:
            row = WorklistEntry(
                patient_name=entry.get('PatientName'),
                patient_id=entry.get('PatientID'),
                patient_birthdate=entry.get('PatientBirthDate'),
                study_description=entry.get('StudyDescription'),
                modality=entry.get('Modality'),
                scheduled_date=entry.get('ScheduledProcedureStepStartDate'),
                scheduled_time=entry.get('ScheduledProcedureStepStartTime'),
                accession_number=entry.get('AccessionNumber'),
                expected_delivery_date=entry.get('ExpectedDeliveryDate'),
            )
            s.add(row)
        else:
            row.patient_name = entry.get('PatientName')
            row.patient_id = entry.get('PatientID')
            row.patient_birthdate = entry.get('PatientBirthDate')
            row.study_description = entry.get('StudyDescription')
            row.modality = entry.get('Modality')
            row.scheduled_date = entry.get('ScheduledProcedureStepStartDate')
            row.scheduled_time = entry.get('ScheduledProcedureStepStartTime')
            row.expected_delivery_date = entry.get('ExpectedDeliveryDate')
        s.commit()
        return row.id
    finally:
        s.close()


def get_entry_by_id(entry_id: int):
    s = Session()
    try:
        row = s.query(WorklistEntry).get(entry_id)
        return row.to_dict() if row else None
    finally:
        s.close()


def update_entry_by_id(entry_id: int, entry: dict):
    s = Session()
    try:
        row = s.query(WorklistEntry).get(entry_id)
        if not row:
            return None
        row.patient_name = entry.get('PatientName')
        row.patient_id = entry.get('PatientID')
        row.patient_birthdate = entry.get('PatientBirthDate')
        row.study_description = entry.get('StudyDescription')
        row.modality = entry.get('Modality')
        row.scheduled_date = entry.get('ScheduledProcedureStepStartDate')
        row.scheduled_time = entry.get('ScheduledProcedureStepStartTime')
        # allow updating accession_number if provided
        if entry.get('AccessionNumber'):
            row.accession_number = entry.get('AccessionNumber')
        s.commit()
        return row.to_dict()
    finally:
        s.close()


def get_entry_by_accession(accession_number: str):
    s = Session()
    try:
        if not accession_number:
            return None
        row = s.query(WorklistEntry).filter_by(accession_number=accession_number).first()
        return row.to_dict() if row else None
    finally:
        s.close()


def delete_entry_by_id(entry_id: int):
    s = Session()
    try:
        row = s.query(WorklistEntry).get(entry_id)
        if row:
            s.delete(row)
            s.commit()
            return True
        return False
    finally:
        s.close()


def delete_entry_by_accession(accession_number: str):
    s = Session()
    try:
        if not accession_number:
            return False
        row = s.query(WorklistEntry).filter_by(accession_number=accession_number).first()
        if row:
            s.delete(row)
            s.commit()
            return True
        return False
    finally:
        s.close()


def clear_all():
    s = Session()
    try:
        s.query(WorklistEntry).delete()
        s.commit()
    finally:
        s.close()


_ACC_RE = re.compile(r'^ACC(\d+)(?:-svc(\d+))?$', re.IGNORECASE)


def _parse_accession_parts(accession_number: str):
    """Trả về (appt_id, svc_id_or_none). svc_id_or_none None nghĩa là dòng ACC... trần (fallback)."""
    if not accession_number:
        return None, None
    m = _ACC_RE.match(accession_number.strip())
    if not m:
        return None, None
    appt = int(m.group(1), 10)
    svc = int(m.group(2), 10) if m.group(2) is not None else None
    return appt, svc


def dedupe_mwl_entry_dicts(entries: list) -> list:
    """
    Loại trùng thừa giữa fallback và chỉ định CLS:
    nếu đã có ít nhất một ACC<id>-svc* thì bỏ các dòng ACC<id> trần (cùng lịch).
    Nhiều chỉ định khác nhau (ACC<id>-svc5, -svc7, ...) giữ nguyên tất cả.
    """
    if not entries:
        return []
    appt_has_svc = set()
    for e in entries:
        appt, svc = _parse_accession_parts(e.get('AccessionNumber') or '')
        if appt is not None and svc is not None:
            appt_has_svc.add(appt)
    out = []
    for e in entries:
        appt, svc = _parse_accession_parts(e.get('AccessionNumber') or '')
        if appt is not None and svc is None and appt in appt_has_svc:
            continue
        out.append(e)
    return out


def remove_duplicate_mwl_rows() -> int:
    """
    Xóa dòng ACC<id> trần khi trong DB đã có bất kỳ ACC<id>-svc* nào (cùng lịch).
    Không gộp các dòng -svc khác nhau.
    """
    init_db()
    rows = get_all_entries() or []
    appt_has_svc = set()
    for r in rows:
        appt, svc = _parse_accession_parts(r.get('AccessionNumber') or '')
        if appt is not None and svc is not None:
            appt_has_svc.add(appt)
    removed = 0
    for r in rows:
        appt, svc = _parse_accession_parts(r.get('AccessionNumber') or '')
        if appt is None or svc is not None:
            continue
        if appt not in appt_has_svc:
            continue
        rid = r.get('id')
        if rid is not None and delete_entry_by_id(int(rid)):
            removed += 1
    return removed
