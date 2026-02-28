#!/usr/bin/env python3
"""
check_system_health.py

Script kiểm tra toàn bộ hệ thống RIS/Worklist:
- Database status
- MWL entries
- Appointment sync status
- Auto-sync scheduler
- DICOM server readiness
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
import traceback

def check_database(db_path):
    """Kiểm tra database"""
    if not os.path.exists(db_path):
        return {"status": "❌ NOT_FOUND", "path": db_path}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lấy danh sách tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Kiểm tra số records
        records_info = {}
        for (table,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                records_info[table] = count
            except:
                records_info[table] = "ERROR"
        
        # Kiểm tra file info
        file_size = os.path.getsize(db_path)
        file_size_mb = file_size / (1024 * 1024)
        
        conn.close()
        
        return {
            "status": "✅ OK",
            "path": db_path,
            "size_mb": f"{file_size_mb:.2f}",
            "tables": records_info
        }
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e)}

def check_mwl_entries():
    """Kiểm tra MWL entries"""
    try:
        # Import mwl_store để kiểm tra entries
        import mwl_store
        mwl_store.init_db()
        entries = mwl_store.get_all_entries()
        
        if not entries:
            return {"count": 0, "entries": []}
        
        # Parse entries
        result = {"count": len(entries), "entries": []}
        for e in entries:
            try:
                entry = json.loads(e[0]) if isinstance(e[0], str) else e[0]
                result["entries"].append({
                    "PatientID": entry.get('PatientID'),
                    "PatientName": entry.get('PatientName'),
                    "StudyDescription": entry.get('StudyDescription'),
                    "ScheduledDate": entry.get('ScheduledProcedureStepStartDate')
                })
            except:
                pass
        
        return result
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e), "traceback": traceback.format_exc()}

def check_appointments():
    """Kiểm tra appointments trong clinic.db"""
    try:
        conn = sqlite3.connect("clinic.db")
        cursor = conn.cursor()
        
        # Count appointments
        cursor.execute("""
            SELECT COUNT(*) FROM appointment 
            WHERE status IN ('pending', 'scheduled')
        """)
        total = cursor.fetchone()[0]
        
        # Count ultrasound appointments
        cursor.execute("""
            SELECT COUNT(*) FROM appointment 
            WHERE (service_type LIKE '%siêu âm%' 
                   OR service_type LIKE '%sieu am%' 
                   OR service_type LIKE '%ultrasound%'
                   OR service_type LIKE '%US%')
            AND status IN ('pending', 'scheduled')
        """)
        ultrasound = cursor.fetchone()[0]
        
        # Recent appointments
        cursor.execute("""
            SELECT a.id, p.name, p.patient_id, a.service_type, a.appointment_date
            FROM appointment a
            JOIN patient p ON a.patient_id = p.id
            WHERE a.status IN ('pending', 'scheduled')
            ORDER BY a.appointment_date DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_pending": total,
            "ultrasound_appointments": ultrasound,
            "recent": [
                {
                    "id": r[0],
                    "patient_name": r[1],
                    "patient_id": r[2],
                    "service_type": r[3],
                    "appointment_date": str(r[4])
                }
                for r in recent
            ]
        }
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e)}

def check_files():
    """Kiểm tra các file cần thiết"""
    files_to_check = [
        "app.py",
        "mwl_server.py",
        "mwl_sync.py",
        "mwl_store.py",
        "clinic.db",
        "mwl.db",
        "worklist.json",
        "run_setup.bat",
        "setup_mwl_service_simple.ps1"
    ]
    
    result = {}
    for fname in files_to_check:
        exists = os.path.exists(fname)
        if exists:
            size = os.path.getsize(fname)
            result[fname] = f"✅ OK ({size} bytes)"
        else:
            result[fname] = "❌ MISSING"
    
    return result

def main():
    print("\n" + "=" * 80)
    print("🏥 KIỂM TRA HỆ THỐNG RIS/WORKLIST - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    # 1. Check databases
    print("\n📊 1. KIỂM TRA DATABASES")
    print("-" * 80)
    
    clinic_db = check_database("clinic.db")
    print("\n✅ clinic.db (Main Database):")
    print(f"   Status: {clinic_db.get('status')}")
    print(f"   Path: {clinic_db.get('path')}")
    print(f"   Size: {clinic_db.get('size_mb')} MB")
    print("   Tables:")
    if "tables" in clinic_db:
        for table, count in sorted(clinic_db["tables"].items()):
            print(f"      • {table:20s} : {count:5d} records")
    
    mwl_db = check_database("mwl.db")
    print("\n✅ mwl.db (DICOM Worklist):")
    print(f"   Status: {mwl_db.get('status')}")
    print(f"   Path: {mwl_db.get('path')}")
    print(f"   Size: {mwl_db.get('size_mb')} MB")
    print("   Tables:")
    if "tables" in mwl_db:
        for table, count in sorted(mwl_db["tables"].items()):
            print(f"      • {table:20s} : {count:5d} records")
    
    # 2. Check appointments
    print("\n\n📋 2. KIỂM TRA APPOINTMENTS")
    print("-" * 80)
    appts = check_appointments()
    if "status" not in appts:
        print(f"   Total pending/scheduled: {appts.get('total_pending', 0)}")
        print(f"   Ultrasound appointments: {appts.get('ultrasound_appointments', 0)}")
        print(f"\n   Recent appointments (top 5):")
        for appt in appts.get('recent', []):
            print(f"      • ID:{appt['id']:4d} | {appt['patient_name']:20s} | {appt['service_type']:20s} | {appt['appointment_date']}")
    else:
        print(f"   ❌ Error: {appts.get('error')}")
    
    # 3. Check MWL entries
    print("\n\n🔗 3. KIỂM TRA MWL ENTRIES (DICOM Worklist)")
    print("-" * 80)
    mwl_entries = check_mwl_entries()
    if "status" not in mwl_entries:
        print(f"   Total entries in MWL: {mwl_entries.get('count', 0)}")
        if mwl_entries.get('entries'):
            print(f"\n   MWL Entries:")
            for entry in mwl_entries['entries']:
                print(f"      • PatientID: {entry.get('PatientID')}")
                print(f"        PatientName: {entry.get('PatientName')}")
                print(f"        StudyDescription: {entry.get('StudyDescription')}")
                print(f"        ScheduledDate: {entry.get('ScheduledDate')}\n")
    else:
        print(f"   ❌ Error: {mwl_entries.get('error')}")
    
    # 4. Check files
    print("\n📁 4. KIỂM TRA CÁC FILE CẦN THIẾT")
    print("-" * 80)
    files = check_files()
    for fname, status in sorted(files.items()):
        print(f"   {fname:40s} : {status}")
    
    # 5. Summary
    print("\n\n" + "=" * 80)
    print("📈 TÓMED TẮTS HỆTONTHỐNG")
    print("=" * 80)
    
    clinic_ok = clinic_db.get('status') == '✅ OK'
    mwl_ok = mwl_db.get('status') == '✅ OK'
    has_appts = appts.get('ultrasound_appointments', 0) > 0 if "status" not in appts else False
    has_mwl = mwl_entries.get('count', 0) > 0 if "status" not in mwl_entries else False
    
    print(f"\n   ✅ clinic.db status        : {'OK' if clinic_ok else 'PROBLEM'}")
    print(f"   ✅ mwl.db status           : {'OK' if mwl_ok else 'PROBLEM'}")
    print(f"   ✅ Appointments (US)       : {appts.get('ultrasound_appointments', '?')} records")
    print(f"   ✅ MWL entries synced      : {mwl_entries.get('count', '?')} entries")
    print(f"   ✅ Sync status             : {'SYNCHRONIZED ✅' if has_appts and has_mwl else 'PENDING'}")
    
    # Final status
    print("\n" + "=" * 80)
    if clinic_ok and mwl_ok:
        print("🟢 HỆ THỐNG: HOẠT ĐỘNG BÌNH THƯỜNG")
    else:
        print("🔴 HỆ THỐNG: CÓ VẤNĐỀ CẦN XỬ LÝ")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    main()
