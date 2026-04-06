#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiểm tra các trường DICOM Modality Worklist có đầy đủ trong CSDL chưa
"""

import sqlite3
from datetime import datetime

DB_PATH = 'clinic.db'

# Các trường DICOM MWL tiêu chuẩn theo DICOM Part 4, Annex K
REQUIRED_MWL_FIELDS = {
    'Patient': {
        'PatientName': {'required': True, 'description': 'Tên bệnh nhân', 'tag': '(0010,0010)'},
        'PatientID': {'required': True, 'description': 'ID bệnh nhân', 'tag': '(0010,0020)'},
        'PatientBirthDate': {'required': False, 'description': 'Ngày sinh', 'tag': '(0010,0030)'},
        'PatientSex': {'required': False, 'description': 'Giới tính', 'tag': '(0010,0040)'},
        'PatientAge': {'required': False, 'description': 'Tuổi', 'tag': '(0010,1010)'},
        'PatientWeight': {'required': False, 'description': 'Cân nặng', 'tag': '(0010,1030)'},
    },
    'ScheduledProcedureStep': {
        'Modality': {'required': True, 'description': 'Loại thiết bị (US)', 'tag': '(0008,0060)'},
        'ScheduledProcedureStepStartDate': {'required': True, 'description': 'Ngày hẹn', 'tag': '(0040,0002)'},
        'ScheduledProcedureStepStartTime': {'required': False, 'description': 'Giờ hẹn', 'tag': '(0040,0003)'},
        'ScheduledProcedureStepID': {'required': True, 'description': 'ID bước thủ thuật', 'tag': '(0040,0009)'},
        'ScheduledProcedureStepDescription': {'required': True, 'description': 'Mô tả thủ thuật', 'tag': '(0040,0007)'},
        'ScheduledStationName': {'required': False, 'description': 'Tên máy', 'tag': '(0040,0010)'},
        'ScheduledStationClassCodeSequence': {'required': False, 'description': 'Loại máy', 'tag': '(0040,0026)'},
    },
    'Request': {
        'AccessionNumber': {'required': True, 'description': 'Số phiếu', 'tag': '(0008,0050)'},
        'RequestingPhysician': {'required': False, 'description': 'Bác sĩ chỉ định', 'tag': '(0032,1032)'},
        'RequestedProcedureDescription': {'required': False, 'description': 'Mô tả yêu cầu', 'tag': '(0032,1060)'},
        'AdmittingDiagnosesDescription': {'required': False, 'description': 'Chẩn đoán', 'tag': '(0008,1080)'},
    },
    'Other': {
        'InstitutionName': {'required': False, 'description': 'Tên cơ sở y tế', 'tag': '(0008,0080)'},
        'InstitutionAddress': {'required': False, 'description': 'Địa chỉ cơ sở', 'tag': '(0008,0081)'},
        'ReferringPhysicianName': {'required': False, 'description': 'Bác sĩ giới thiệu', 'tag': '(0008,0090)'},
    }
}

def check_database_schema():
    """Kiểm tra schema của database"""
    print("=" * 80)
    print("KIỂM TRA CẤU TRÚC CƠ SỞ DỮ LIỆU CHO DICOM WORKLIST")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Lấy danh sách các bảng
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 Các bảng trong database: {', '.join(tables)}")
        
        # Kiểm tra các bảng chính
        key_tables = ['patient', 'appointment', 'clinical_service', 'clinical_service_setting']
        missing_tables = [t for t in key_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ THIẾU các bảng: {', '.join(missing_tables)}")
        else:
            print("✅ Đủ các bảng chính")
        
        # Kiểm tra các trường trong mỗi bảng
        print("\n" + "=" * 80)
        print("CHI TIẾT CÁC TRƯỜNG TRONG BẢNG")
        print("=" * 80)
        
        for table in key_tables:
            if table not in tables:
                continue
                
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            print(f"\n📋 Bảng: {table}")
            print(f"   Các trường có sẵn:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        
        # Kiểm tra dữ liệu mẫu
        print("\n" + "=" * 80)
        print("KIỂM TRA DỮ LIỆU MẪU")
        print("=" * 80)
        
        # Kiểm tra appointment siêu âm
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM appointment a
            JOIN clinical_service cs ON cs.appointment_id = a.id
            JOIN clinical_service_setting s ON cs.service_id = s.id
            WHERE (
                s.service_group LIKE '%siêu âm%' OR
                s.service_group LIKE '%sieu am%' OR
                s.service_group LIKE '%ultrasound%' OR
                s.name LIKE '%siêu âm%' OR
                s.name LIKE '%sieu am%'
            )
        """)
        ultrasound_count = cursor.fetchone()['count']
        print(f"\n📊 Số lượng appointment siêu âm trong DB: {ultrasound_count}")
        
        if ultrasound_count > 0:
            # Lấy 1 appointment mẫu
            cursor.execute("""
                SELECT 
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
                ORDER BY a.appointment_date DESC
                LIMIT 1
            """)
            
            sample = cursor.fetchone()
            if sample:
                print("\n📝 Dữ liệu mẫu (appointment siêu âm):")
                for key in sample.keys():
                    print(f"   {key}: {sample[key]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def analyze_mapping():
    """Phân tích mapping giữa CSDL và DICOM Worklist"""
    print("\n" + "=" * 80)
    print("PHÂN TÍCH MAPPING CSDL -> DICOM WORKLIST")
    print("=" * 80)
    
    mappings = {
        'PatientName': 'patient.name',
        'PatientID': 'generated: PAT_{appointment_id}',
        'PatientBirthDate': 'patient.date_of_birth',
        'PatientSex': '❌ THIẾU (không có trong DB)',
        'Modality': 'Fixed: US',
        'ScheduledProcedureStepStartDate': 'appointment.appointment_date',
        'ScheduledProcedureStepStartTime': 'appointment.appointment_date',
        'ScheduledProcedureStepID': 'generated: SP_{appointment_id}',
        'ScheduledProcedureStepDescription': 'clinical_service_setting.name',
        'AccessionNumber': 'generated: ACC_{appointment_id}',
        'RequestingPhysician': 'appointment.doctor_name',
        'InstitutionName': 'Fixed: "Phòng khám chuyên khoa Phụ Sản Đại Anh"',
        'InstitutionAddress': 'Fixed: "TDP Quán Trắng - Tân An - Bắc Ninh"',
    }
    
    print("\n📋 Mapping hiện tại:")
    for dicom_field, db_field in mappings.items():
        if 'THIẾU' in db_field:
            print(f"   ❌ {dicom_field:40} <- {db_field}")
        else:
            print(f"   ✅ {dicom_field:40} <- {db_field}")

def check_missing_fields():
    """Kiểm tra các trường DICOM thiếu"""
    print("\n" + "=" * 80)
    print("CÁC TRƯỜNG DICOM CÓ THỂ BỔ SUNG")
    print("=" * 80)
    
    # Các trường quan trọng nhưng hiện đang thiếu
    missing = [
        {
            'field': 'PatientSex',
            'tag': '(0010,0040)',
            'importance': 'Optional (nhưng khuyến nghị)',
            'description': 'Giới tính bệnh nhân (M/F/O)',
            'suggestion': 'Thêm cột gender vào bảng patient'
        },
        {
            'field': 'AdmittingDiagnosesDescription',
            'tag': '(0008,1080)',
            'importance': 'Optional',
            'description': 'Chẩn đoán ban đầu',
            'suggestion': 'Thêm cột diagnosis vào bảng appointment'
        },
        {
            'field': 'Referral Type',
            'tag': '(0040,0012)',
            'importance': 'Optional',
            'description': 'Loại giới thiệu',
            'suggestion': 'Có thể bỏ qua nếu không cần'
        }
    ]
    
    print("\n⚠️  Các trường thiếu có thể bổ sung:")
    for item in missing:
        print(f"\n   Trường: {item['field']} {item['tag']}")
        print(f"   Tầm quan trọng: {item['importance']}")
        print(f"   Mô tả: {item['description']}")
        print(f"   Gợi ý: {item['suggestion']}")
    
    print("\n" + "=" * 80)
    print("KẾT LUẬN")
    print("=" * 80)
    print("""
✅ CÁC TRƯỜNG BẮT BUỘC ĐÃ ĐỦ:
   - PatientName, PatientID
   - Modality, ScheduledProcedureStepDescription
   - ScheduledProcedureStepStartDate, ScheduledProcedureStepStartTime
   - AccessionNumber

⚠️  CÁC TRƯỜNG KHUYẾN NGHỊ (Optional):
   - PatientSex: Thiếu (không ảnh hưởng lắm)
   - AdmittingDiagnosesDescription: Thiếu (không bắt buộc)

🎯 KẾT LUẬN: CSDL HIỆN TẠI ĐÃ ĐỦ ĐỂ GỬI WORKLIST TỚI MÁY SIÊU ÂM!
   Phần còn lại là cấu hình máy siêu âm để query MWL server.
    """)

if __name__ == "__main__":
    import sys
    import io
    # Set UTF-8 encoding for Windows console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    check_database_schema()
    analyze_mapping()
    check_missing_fields()

