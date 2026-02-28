#!/usr/bin/env python3
"""
Script test tích hợp đồng bộ Voluson E10
Kiểm tra các chức năng cơ bản của hệ thống đồng bộ
"""

import sys
import os
import json
import sqlite3
from datetime import datetime, timedelta

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test kết nối database"""
    print("🔍 Kiểm tra kết nối database...")
    
    try:
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        
        # Kiểm tra bảng appointment
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointment'")
        if not cursor.fetchone():
            print("❌ Bảng 'appointment' không tồn tại")
            return False
            
        # Kiểm tra cột voluson_synced
        cursor.execute("PRAGMA table_info(appointment)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'voluson_synced' not in columns:
            print("⚠️  Cột 'voluson_synced' chưa tồn tại, sẽ được tạo tự động")
        else:
            print("✅ Cột 'voluson_synced' đã tồn tại")
            
        conn.close()
        print("✅ Kết nối database thành công")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return False

def test_config_file():
    """Test file cấu hình"""
    print("\n🔍 Kiểm tra file cấu hình...")
    
    try:
        if os.path.exists('voluson_config.json'):
            with open('voluson_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("✅ File cấu hình tồn tại")
            print(f"   - IP máy siêu âm: {config.get('voluson_ip', 'N/A')}")
            print(f"   - Port: {config.get('voluson_port', 'N/A')}")
            print(f"   - Đồng bộ bật: {config.get('sync_enabled', False)}")
            return True
        else:
            print("⚠️  File cấu hình chưa tồn tại, sẽ được tạo tự động")
            return True
    except Exception as e:
        print(f"❌ Lỗi đọc file cấu hình: {e}")
        return False

def test_voluson_service():
    """Test service đồng bộ"""
    print("\n🔍 Kiểm tra service đồng bộ...")
    
    try:
        from voluson_sync_service import get_voluson_sync_service
        
        service = get_voluson_sync_service()
        print("✅ Service đồng bộ khởi tạo thành công")
        
        # Test lấy trạng thái
        status = service.get_sync_status()
        print(f"   - Tổng cuộc hẹn: {status.get('total_appointments', 0)}")
        print(f"   - Đã đồng bộ: {status.get('synced_appointments', 0)}")
        print(f"   - Chờ đồng bộ: {status.get('pending_appointments', 0)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Không thể import service: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi service: {e}")
        return False

def test_appointment_data():
    """Test dữ liệu cuộc hẹn"""
    print("\n🔍 Kiểm tra dữ liệu cuộc hẹn...")
    
    try:
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        
        # Lấy cuộc hẹn gần đây
        cursor.execute("""
            SELECT 
                a.id,
                a.appointment_date,
                a.service_type,
                a.doctor_name,
                p.name,
                p.phone,
                p.date_of_birth,
                p.address,
                a.voluson_synced
            FROM appointment a
            JOIN patient p ON a.patient_id = p.id
            WHERE a.appointment_date >= datetime('now')
            ORDER BY a.appointment_date DESC
            LIMIT 5
        """)
        
        appointments = cursor.fetchall()
        
        if not appointments:
            print("⚠️  Không có cuộc hẹn nào trong database")
            return True
            
        print(f"✅ Tìm thấy {len(appointments)} cuộc hẹn gần đây:")
        
        for apt in appointments:
            sync_status = "Đã đồng bộ" if apt[8] else "Chờ đồng bộ"
            print(f"   - ID {apt[0]}: {apt[4]} ({apt[5]}) - {sync_status}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kiểm tra dữ liệu: {e}")
        return False

def test_dependencies():
    """Test các thư viện cần thiết"""
    print("\n🔍 Kiểm tra thư viện cần thiết...")
    
    required_modules = [
        'pydicom',
        'pynetdicom',
        'flask',
        'sqlite3'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - CHƯA CÀI ĐẶT")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  Cần cài đặt: pip install {' '.join(missing_modules)}")
        return False
    
    return True

def create_test_appointment():
    """Tạo cuộc hẹn test"""
    print("\n🔍 Tạo cuộc hẹn test...")
    
    try:
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        
        # Tạo bệnh nhân test
        test_patient = {
            'name': 'Bệnh nhân Test',
            'phone': '0123456789',
            'address': 'Địa chỉ test',
            'date_of_birth': '1990-01-01'
        }
        
        # Kiểm tra bệnh nhân đã tồn tại chưa
        cursor.execute("SELECT id FROM patient WHERE phone = ?", (test_patient['phone'],))
        patient_id = cursor.fetchone()
        
        if not patient_id:
            cursor.execute("""
                INSERT INTO patient (name, phone, address, date_of_birth, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (test_patient['name'], test_patient['phone'], 
                  test_patient['address'], test_patient['date_of_birth']))
            patient_id = cursor.lastrowid
        else:
            patient_id = patient_id[0]
        
        # Tạo cuộc hẹn test
        tomorrow = datetime.now() + timedelta(days=1)
        appointment_date = tomorrow.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO appointment (patient_id, appointment_date, service_type, doctor_name, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (patient_id, appointment_date, 'Siêu âm thai', 'BS Test'))
        
        conn.commit()
        conn.close()
        
        print("✅ Đã tạo cuộc hẹn test thành công")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tạo cuộc hẹn test: {e}")
        return False

def main():
    """Hàm main test"""
    print("=" * 60)
    print("    TEST TÍCH HỢP VOLUSON E10 SYNC")
    print("    Phòng khám chuyên khoa Phụ Sản Đại Anh")
    print("=" * 60)
    
    tests = [
        ("Database", test_database_connection),
        ("Config", test_config_file),
        ("Dependencies", test_dependencies),
        ("Service", test_voluson_service),
        ("Data", test_appointment_data),
        ("Test Appointment", create_test_appointment)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Lỗi trong test {test_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"KẾT QUẢ: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 TẤT CẢ TESTS THÀNH CÔNG!")
        print("\n📋 HƯỚNG DẪN TIẾP THEO:")
        print("1. Cấu hình IP máy siêu âm trong voluson_config.json")
        print("2. Khởi động ứng dụng Flask: python app.py")
        print("3. Truy cập: http://localhost:5000/voluson-sync-admin.html")
        print("4. Hoặc chạy daemon: python start_voluson_sync.py")
    else:
        print("⚠️  MỘT SỐ TESTS THẤT BẠI")
        print("Vui lòng kiểm tra và sửa lỗi trước khi sử dụng")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
