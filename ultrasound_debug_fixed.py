#!/usr/bin/env python3
"""
Script debug kết nối máy siêu âm - Phiên bản sửa lỗi
Kiểm tra chi tiết các vấn đề kết nối
"""

import socket
import subprocess
import sys
import time
from pynetdicom import AE, VerificationPresentationContexts
import pydicom
from pydicom.uid import generate_uid

def test_ping(ip):
    """Test ping đến IP"""
    print(f"🔍 Test ping đến {ip}...")
    try:
        result = subprocess.run(['ping', '-n', '1', ip], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Ping {ip} thành công")
            return True
        else:
            print(f"❌ Ping {ip} thất bại")
            print(f"Output: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Lỗi ping: {e}")
        return False

def test_port(ip, port):
    """Test kết nối TCP đến port"""
    print(f"🔍 Test kết nối TCP {ip}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} mở")
            return True
        else:
            print(f"❌ Port {port} đóng hoặc bị chặn")
            return False
    except Exception as e:
        print(f"❌ Lỗi test port: {e}")
        return False

def test_dicom_connection(ip, port, ae_title):
    """Test kết nối DICOM"""
    print(f"🔍 Test kết nối DICOM {ip}:{port}...")
    try:
        # Tạo AE với UID đúng cách
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        print(f"   Đang kết nối đến {ip}:{port} với AE Title: {ae_title}")
        
        # Test kết nối với timeout ngắn
        assoc = ae.associate(ip, port, ae_title=ae_title)
        
        if assoc.is_established:
            print(f"✅ DICOM Association thành công")
            assoc.release()
            return True
        else:
            print(f"❌ DICOM Association thất bại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi DICOM: {e}")
        return False

def test_simple_dicom():
    """Test DICOM đơn giản hơn"""
    print(f"🔍 Test DICOM đơn giản...")
    try:
        from pynetdicom import AE, VerificationPresentationContexts
        
        # Tạo AE đơn giản
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        print(f"   AE Title: {ae.ae_title}")
        print(f"   Requested contexts: {len(ae.requested_contexts)}")
        
        # Test kết nối
        assoc = ae.associate('10.17.2.1', 104, ae_title='Maysieuam_E10')
        
        if assoc.is_established:
            print(f"✅ DICOM kết nối thành công!")
            assoc.release()
            return True
        else:
            print(f"❌ DICOM kết nối thất bại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi DICOM đơn giản: {e}")
        return False

def check_network_config():
    """Kiểm tra cấu hình mạng"""
    print("🔍 Kiểm tra cấu hình mạng...")
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        print("📋 Cấu hình mạng hiện tại:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Lỗi kiểm tra mạng: {e}")

def main():
    """Hàm chính"""
    print("🏥 ULTRASOUND DEBUG SCRIPT - PHIÊN BẢN SỬA LỖI")
    print("=" * 60)
    
    # Cấu hình
    ultrasound_ip = "10.17.2.1"
    ultrasound_port = 104
    ultrasound_ae_title = "Maysieuam_E10"
    
    print(f"📋 Cấu hình test:")
    print(f"   IP máy siêu âm: {ultrasound_ip}")
    print(f"   Port: {ultrasound_port}")
    print(f"   AE Title (máy): {ultrasound_ae_title}")
    print()
    
    # Test các bước
    tests = [
        ("Ping", lambda: test_ping(ultrasound_ip)),
        ("Port TCP", lambda: test_port(ultrasound_ip, ultrasound_port)),
        ("DICOM Simple", lambda: test_simple_dicom()),
        ("DICOM Full", lambda: test_dicom_connection(ultrasound_ip, ultrasound_port, ultrasound_ae_title))
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ Lỗi trong {name}: {e}")
            results[name] = False
        time.sleep(1)
    
    # Tổng kết
    print(f"\n{'='*60}")
    print("📊 TỔNG KẾT DEBUG")
    print(f"{'='*60}")
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nKết quả: {passed}/{total} tests passed")
    
    if passed >= 2:  # Ping + Port thành công
        print("\n🎉 KẾT NỐI CƠ BẢN THÀNH CÔNG!")
        print("Ping và Port đều hoạt động tốt.")
        print("Vấn đề có thể là:")
        print("1. AE Title không khớp trên máy siêu âm")
        print("2. DICOM service chưa được cấu hình đúng")
        print("3. Cần kiểm tra cấu hình DICOM trên máy siêu âm")
    else:
        print("\n⚠️ CÓ LỖI KẾT NỐI CƠ BẢN")
        print("Vui lòng kiểm tra mạng và máy siêu âm")

if __name__ == "__main__":
    main()
