#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test chuc nang tu dong gui worklist khi them dich vu sieu am
"""

import sqlite3
import sys
import os
from voluson_sync_service import get_voluson_sync_service

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_worklist_sync():
    """Test chuc nang dong bo worklist"""
    print("=" * 60)
    print("TEST CHUC NANG DONG BO WORKLIST VOLUSON E10")
    print("=" * 60)
    
    # Ket noi database
    db_path = 'clinic.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Kiem tra cau hinh Voluson
    print("\n1. KIEM TRA CAU HINH VOLUSON:")
    print("-" * 60)
    sync_service = get_voluson_sync_service()
    print(f"Sync enabled: {sync_service.sync_enabled}")
    print(f"Voluson IP: {sync_service.voluson_ip}")
    print(f"Voluson Port: {sync_service.voluson_port}")
    print(f"AE Title: {sync_service.ae_title}")
    print(f"Voluson AE Title: {sync_service.voluson_ae_title}")
    
    # 2. Tim cac dich vu sieu am
    print("\n2. TIM CAC DICH VU SIEU AM:")
    print("-" * 60)
    cursor.execute("""
        SELECT id, name, service_group, provider_unit
        FROM clinical_service_setting
        WHERE service_group LIKE '%siêu âm%' 
           OR service_group LIKE '%sieu am%'
           OR service_group LIKE '%ultrasound%'
           OR name LIKE '%siêu âm%'
           OR name LIKE '%sieu am%'
        LIMIT 10
    """)
    services = cursor.fetchall()
    if services:
        print(f"Tim thay {len(services)} dich vu sieu am:")
        for svc in services:
            svc_name = svc[1] if svc[1] else 'N/A'
            svc_group = svc[2] if svc[2] else 'N/A'
            print(f"  - ID: {svc[0]}, Name: {svc_name}, Group: {svc_group}")
    else:
        print("Khong tim thay dich vu sieu am nao!")
        print("Cac dich vu hien co:")
        cursor.execute("SELECT id, name, service_group FROM clinical_service_setting LIMIT 10")
        for svc in cursor.fetchall():
            svc_name = svc[1] if svc[1] else 'N/A'
            svc_group = svc[2] if svc[2] else 'N/A'
            print(f"  - ID: {svc[0]}, Name: {svc_name}, Group: {svc_group}")
    
    # 3. Tim appointment co dich vu sieu am gan nhat
    print("\n3. TIM APPOINTMENT CO DICH VU SIEU AM:")
    print("-" * 60)
    cursor.execute("""
        SELECT DISTINCT
            a.id,
            a.appointment_date,
            p.name as patient_name,
            s.name as service_name,
            s.service_group
        FROM appointment a
        JOIN patient p ON a.patient_id = p.id
        JOIN clinical_service cs ON cs.appointment_id = a.id
        JOIN clinical_service_setting s ON cs.service_id = s.id
        WHERE (s.service_group LIKE '%siêu âm%' 
           OR s.service_group LIKE '%sieu am%'
           OR s.service_group LIKE '%ultrasound%'
           OR s.name LIKE '%siêu âm%'
           OR s.name LIKE '%sieu am%')
        AND a.appointment_date >= date('now')
        ORDER BY a.appointment_date DESC
        LIMIT 5
    """)
    appointments = cursor.fetchall()
    if appointments:
        print(f"Tim thay {len(appointments)} appointment co dich vu sieu am:")
        for apt in appointments:
            print(f"  - Appointment ID: {apt[0]}")
            print(f"    Date: {apt[1]}")
            print(f"    Patient: {apt[2] if apt[2] else 'N/A'}")
            print(f"    Service: {apt[3] if apt[3] else 'N/A'} (Group: {apt[4] if apt[4] else 'N/A'})")
            
            # Kiem tra trang thai sync
            cursor.execute("""
                SELECT voluson_synced, voluson_sync_time
                FROM appointment
                WHERE id = ?
            """, (apt[0],))
            sync_status = cursor.fetchone()
            if sync_status:
                print(f"    Voluson Synced: {sync_status[0]}, Time: {sync_status[1]}")
    else:
        print("Khong tim thay appointment nao co dich vu sieu am!")
    
    # 4. Test ket noi Voluson
    print("\n4. TEST KET NOI VOLUSON:")
    print("-" * 60)
    if sync_service.test_connection():
        print("✅ Ket noi thanh cong!")
    else:
        print("❌ Ket noi that bai!")
        print("   Hay kiem tra:")
        print("   - DICOM server dang chay (python dicom_server_simple.py)")
        print("   - IP va Port cua Voluson dung")
        print("   - Network connectivity (ping 10.17.2.1)")
    
    # 5. Neu co appointment, test sync
    if appointments:
        print("\n5. TEST DONG BO WORKLIST:")
        print("-" * 60)
        test_appt_id = appointments[0][0]
        service_name = appointments[0][3]
        print(f"Test sync appointment ID {test_appt_id}...")
        
        if sync_service.add_appointment_to_worklist(
            appointment_id=test_appt_id,
            service_name=service_name,
            modality='US'
        ):
            print("✅ Dong bo thanh cong!")
        else:
            print("❌ Dong bo that bai!")
    
    conn.close()
    print("\n" + "=" * 60)
    print("KET THUC TEST")
    print("=" * 60)

if __name__ == "__main__":
    test_worklist_sync()

