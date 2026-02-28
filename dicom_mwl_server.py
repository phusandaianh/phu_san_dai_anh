#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DICOM Modality Worklist (MWL) Server - Phù hợp pynetdicom 1.5.7
"""

from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind, VerificationSOPClass
from pydicom.dataset import Dataset
from datetime import datetime
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dicom_mwl_server')

DB_PATH = 'clinic.db'

def handle_c_echo(event):
    """Xử lý C-ECHO request"""
    logger.info("Nhận được C-ECHO từ %s", event.assoc.requestor.ae_title)
    return 0x0000  # Success

def handle_c_find(event):
    """Xử lý C-FIND (Worklist)"""
    query = event.identifier
    logger.info("Nhận được C-FIND từ %s", event.assoc.requestor.ae_title)

    modality = query.get('Modality', None)
    date = query.get('ScheduledProcedureStepStartDate', None)
    logger.info("Truy vấn: Modality=%s, Ngày=%s", modality, date)

    for ds in get_worklist_entries(query):
        yield (0xFF00, ds)  # Pending
    yield (0x0000, None)   # Success

def get_worklist_entries(query_dataset):
    entries = []

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT
                a.id as appointment_id,
                a.appointment_date,
                a.service_type,
                a.doctor_name,
                p.name as patient_name,
                p.date_of_birth,
                p.phone,
                p.address,
                s.name as service_name,
                s.service_group
            FROM appointment a
            JOIN patient p ON a.patient_id = p.id
            JOIN clinical_service cs ON cs.appointment_id = a.id
            JOIN clinical_service_setting s ON cs.service_id = s.id
            WHERE (
                s.service_group LIKE '%siêu âm%' OR
                s.service_group LIKE '%sieu am%' OR
                s.service_group LIKE '%ultrasound%' OR
                s.name LIKE '%siêu âm%' OR
                s.name LIKE '%sieu am%'
            )
            AND a.appointment_date >= date('now')
            AND a.appointment_date <= date('now', '+30 days')
            ORDER BY a.appointment_date, a.id
        """)

        rows = cursor.fetchall()
        for row in rows:
            try:
                ds = build_worklist_dataset(row)
                entries.append(ds)
            except Exception as e:
                logger.error("Lỗi tạo worklist entry: %s", e)

        conn.close()
    except Exception as e:
        logger.error("Lỗi truy vấn DB: %s", e)

    return entries

def build_worklist_dataset(row):
    ds = Dataset()
    ds.PatientName = row['patient_name'] or ''
    ds.PatientID = "PAT_%s" % row['appointment_id']
    ds.PatientSex = ''

    if row['date_of_birth']:
        try:
            dob = datetime.strptime(row['date_of_birth'], '%Y-%m-%d').strftime('%Y%m%d')
            ds.PatientBirthDate = dob
        except:
            ds.PatientBirthDate = ''
    else:
        ds.PatientBirthDate = ''

    sps = Dataset()
    sps.Modality = 'US'

    try:
        apt_date = datetime.fromisoformat(row['appointment_date'].replace('Z', '+00:00'))
        sps.ScheduledProcedureStepStartDate = apt_date.strftime('%Y%m%d')
        sps.ScheduledProcedureStepStartTime = apt_date.strftime('%H%M%S')
    except:
        now = datetime.now()
        sps.ScheduledProcedureStepStartDate = now.strftime('%Y%m%d')
        sps.ScheduledProcedureStepStartTime = now.strftime('%H%M%S')

    sps.ScheduledProcedureStepID = "SP_%s" % row['appointment_id']
    sps.ScheduledProcedureStepDescription = row['service_name'] or row['service_type'] or 'Siêu âm'

    ds.ScheduledProcedureStepSequence = [sps]
    ds.RequestingPhysician = row['doctor_name'] or ''
    ds.AccessionNumber = "ACC_%s" % row['appointment_id']
    ds.InstitutionName = "Phòng khám chuyên khoa Phụ Sản Đại Anh"
    ds.InstitutionAddress = "TDP Quán Trắng - Tân An - Bắc Ninh"

    return ds

if __name__ == "__main__":
    print("=" * 60)
    print("DICOM MODALITY WORKLIST (MWL) SERVER - pynetdicom 1.5.7")
    print("=" * 60)
    print("AE Title: CLINIC_SYSTEM")
    print("Port: 104")
    print("Database: clinic.db")
    print("=" * 60)

    ae = AE(ae_title='CLINIC_SYSTEM')
    ae.add_supported_context(VerificationSOPClass)
    ae.add_supported_context(ModalityWorklistInformationFind)

    handlers = [
        (evt.EVT_C_ECHO, handle_c_echo),
        (evt.EVT_C_FIND, handle_c_find)
    ]

    try:
        ae.start_server(('0.0.0.0', 104), evt_handlers=handlers, block=True)
    except KeyboardInterrupt:
        print("Đã dừng server.")
    except Exception as e:
        logger.error("Lỗi khởi động server: %s", e)
