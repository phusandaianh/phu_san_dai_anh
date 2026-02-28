#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kiểm tra đồng bộ thông tin bệnh nhân giữa clinic.db và mwl.db
"""

import sqlite3
from datetime import datetime

def check_clinic_db():
    """Kiểm tra bệnh nhân đã đăng ký siêu âm trong clinic.db"""
    print("=" * 80)
    print("THÔNG TIN BỆNH NHÂN TỪ CLINIC.DB (HỆ THỐNG CHÍNH)")
    print("=" * 80)
    
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    
    # Lấy các appointment ngày hôm nay
    today = datetime.now().date()
    query = """
    SELECT 
        p.name,
        p.phone,
        p.patient_id,
        p.date_of_birth,
        a.appointment_date,
        a.service_type,
        a.id
    FROM patient p
    JOIN appointment a ON p.id = a.patient_id
    WHERE DATE(a.appointment_date) = ?
    ORDER BY a.appointment_date
    """
    
    cursor.execute(query, (today,))
    appointments = cursor.fetchall()
    
    if not appointments:
        print(f"Không có appointment nào hôm nay ({today})")
    else:
        print(f"Tổng cộng: {len(appointments)} appointment\n")
        for idx, (name, phone, pid, dob, appt_date, service, appt_id) in enumerate(appointments, 1):
            print(f"{idx}. Bệnh nhân: {name}")
            print(f"   Phone: {phone}")
            print(f"   Patient ID: {pid}")
            print(f"   DOB: {dob}")
            print(f"   Appointment: {appt_date}")
            print(f"   Service: {service}")
            print(f"   Appointment ID: {appt_id}")
            print()
    
    conn.close()

def check_mwl_db():
    """Kiểm tra dữ liệu worklist trong mwl.db"""
    print("\n" + "=" * 80)
    print("THÔNG TIN WORKLIST TỪ MWL.DB (DICOM WORKLIST)")
    print("=" * 80)
    
    try:
        import mwl_store
        entries = mwl_store.get_all_entries()
        
        if not entries:
            print("Không có entries nào trong MWL worklist")
        else:
            print(f"Tổng cộng: {len(entries)} entries\n")
            for idx, entry in enumerate(entries, 1):
                print(f"{idx}. Bệnh nhân: {entry.get('PatientName')}")
                print(f"   Patient ID: {entry.get('PatientID')}")
                print(f"   DOB: {entry.get('PatientBirthDate')}")
                print(f"   Study Description: {entry.get('StudyDescription')}")
                print(f"   Modality: {entry.get('Modality')}")
                print(f"   Scheduled Date: {entry.get('ScheduledProcedureStepStartDate')}")
                print(f"   Scheduled Time: {entry.get('ScheduledProcedureStepStartTime')}")
                print(f"   Accession Number: {entry.get('AccessionNumber')}")
                print()
    except Exception as e:
        print(f"Lỗi khi kiểm tra MWL.db: {e}")

def compare_sync():
    """So sánh dữ liệu giữa clinic.db và mwl.db"""
    print("\n" + "=" * 80)
    print("KIỂM TRA ĐỒNG BỘ")
    print("=" * 80)
    
    # Lấy dữ liệu từ clinic.db
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    today = datetime.now().date()
    
    cursor.execute("""
    SELECT 
        p.name,
        p.phone,
        p.patient_id,
        p.date_of_birth,
        a.appointment_date,
        a.service_type
    FROM patient p
    JOIN appointment a ON p.id = a.patient_id
    WHERE DATE(a.appointment_date) = ?
    ORDER BY a.appointment_date
    """, (today,))
    
    clinic_appts = cursor.fetchall()
    conn.close()
    
    # Lấy dữ liệu từ mwl.db
    try:
        import mwl_store
        mwl_entries = mwl_store.get_all_entries()
    except:
        mwl_entries = []
    
    # So sánh
    print(f"\nClinic.db: {len(clinic_appts)} appointment")
    print(f"MWL.db: {len(mwl_entries)} entries")
    
    if len(clinic_appts) == 0:
        print("\n⚠️  Không có appointment nào trong clinic.db hôm nay")
    elif len(mwl_entries) == 0:
        print("\n⚠️  MWL.db trống! Cần chạy mwl_sync.py để đồng bộ dữ liệu")
    else:
        print("\n✓ Cả hai database đều có dữ liệu")
        
        # Kiểm tra chi tiết
        matched = 0
        for clinic_appt in clinic_appts:
            name, phone, pid, dob, appt_date, service = clinic_appt
            # Tìm trong MWL
            for mwl_entry in mwl_entries:
                if mwl_entry.get('PatientName') and name and name.lower() in mwl_entry.get('PatientName', '').lower():
                    matched += 1
                    print(f"✓ {name} - MATCHED")
                    break
            else:
                print(f"✗ {name} - NOT FOUND in MWL")
        
        print(f"\nKết quả: {matched}/{len(clinic_appts)} bệnh nhân được đồng bộ")

if __name__ == '__main__':
    check_clinic_db()
    check_mwl_db()
    compare_sync()
