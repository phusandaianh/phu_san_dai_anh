"""mwl_store.py

Simple SQLite-backed store for Modality Worklist entries using SQLAlchemy (standalone, not Flask).
Provides basic CRUD and upsert helpers used by mwl_sync.py and mwl_server.py.
"""
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os

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
        }


def init_db():
    if not os.path.exists(DB_FILENAME):
        Base.metadata.create_all(engine)


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


def clear_all():
    s = Session()
    try:
        s.query(WorklistEntry).delete()
        s.commit()
    finally:
        s.close()
