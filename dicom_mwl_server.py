#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DICOM Modality Worklist (MWL) Server - Phù hợp pynetdicom 1.5.7
"""

from pynetdicom import AE, evt
from pynetdicom.sop_class import ModalityWorklistInformationFind, VerificationSOPClass
from pydicom.dataset import Dataset
from datetime import datetime, timedelta
import sqlite3
import logging
import re
import unicodedata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dicom_mwl_server')

DB_PATH = 'mwl.db'

def _ascii_fold(value: str) -> str:
    """
    Convert Vietnamese/Unicode text to ASCII for old modalities that
    don't render UTF-8 in MWL properly.
    """
    s = str(value or '').strip()
    if not s:
        return ''
    s = s.replace('đ', 'd').replace('Đ', 'D')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    # Keep a safe ASCII subset; put '-' at end to avoid regex range issues.
    s = re.sub(r'[^A-Za-z0-9 _./-]', ' ', s)
    s = re.sub(r'\\s+', ' ', s).strip()
    return s

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
    today_yyyymmdd = datetime.now().strftime('%Y%m%d')

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id as entry_id,
                patient_name,
                patient_id,
                patient_birthdate,
                study_description,
                modality,
                scheduled_date,
                scheduled_time,
                accession_number,
                expected_delivery_date
            FROM worklist_entries
            WHERE scheduled_date = ?
              AND (
                lower(ifnull(modality, '')) = 'us'
                OR lower(ifnull(study_description, '')) LIKE '%sieu am%'
                OR lower(ifnull(study_description, '')) LIKE '%ultrasound%'
              )
            ORDER BY scheduled_time, id
        """, (today_yyyymmdd,))

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
    # High compatibility mode for older ultrasound modalities:
    # send ASCII-only strings to avoid garbled Vietnamese diacritics.
    ds.SpecificCharacterSet = ['ISO_IR 6']
    ds.PatientName = _ascii_fold(row['patient_name'] or '')
    ds.PatientID = row['patient_id'] or ("PAT_%s" % row['entry_id'])
    ds.PatientSex = ''

    if row['patient_birthdate']:
        try:
            raw = str(row['patient_birthdate'])
            if len(raw) == 8 and raw.isdigit():
                dob = raw
            else:
                dob = datetime.strptime(raw[:10], '%Y-%m-%d').strftime('%Y%m%d')
            ds.PatientBirthDate = dob
        except:
            ds.PatientBirthDate = ''
    else:
        ds.PatientBirthDate = ''

    sps = Dataset()
    sps.Modality = 'US'

    try:
        sps.ScheduledProcedureStepStartDate = (row['scheduled_date'] or '').strip() or datetime.now().strftime('%Y%m%d')
        sps.ScheduledProcedureStepStartTime = (row['scheduled_time'] or '').strip() or datetime.now().strftime('%H%M%S')
    except:
        now = datetime.now()
        sps.ScheduledProcedureStepStartDate = now.strftime('%Y%m%d')
        sps.ScheduledProcedureStepStartTime = now.strftime('%H%M%S')

    sps.ScheduledProcedureStepID = "SP_%s" % row['entry_id']
    sps.ScheduledProcedureStepDescription = _ascii_fold(row['study_description'] or 'Sieu am')

    ds.ScheduledProcedureStepSequence = [sps]
    ds.RequestingPhysician = ''
    ds.AccessionNumber = row['accession_number'] or ("ACC_%s" % row['entry_id'])
    expected_delivery_date = (row['expected_delivery_date'] or '').strip() if 'expected_delivery_date' in row.keys() else ''
    if expected_delivery_date:
        # Many ultrasound machines display this text directly in MWL details.
        ds.RequestedProcedureDescription = _ascii_fold(f"{row['study_description'] or 'Sieu am'} - DKS {expected_delivery_date}")
        # If modality supports OB fields, derive LastMenstrualDate from EDD (~280 days).
        try:
            edd = datetime.strptime(expected_delivery_date[:10], '%Y-%m-%d').date()
            lmp = edd - timedelta(days=280)
            ds.LastMenstrualDate = lmp.strftime('%Y%m%d')
        except Exception:
            pass
    else:
        ds.RequestedProcedureDescription = _ascii_fold(row['study_description'] or 'Sieu am')
    ds.InstitutionName = "Phong kham chuyen khoa Phu San Dai Anh"
    ds.InstitutionAddress = "TDP Quan Trang - Tan An - Bac Ninh"

    return ds

if __name__ == "__main__":
    print("=" * 60)
    print("DICOM MODALITY WORKLIST (MWL) SERVER - pynetdicom 1.5.7")
    print("=" * 60)
    print("AE Title: CLINIC_SYSTEM")
    print("Port: 104")
    print("Database: mwl.db (worklist_entries)")
    print("Filter: chi dinh sieu am trong ngay hien tai")
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
