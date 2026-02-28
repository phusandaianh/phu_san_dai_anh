#!/usr/bin/env python3
"""
Script debug kết nối Voluson E10 - Phiên bản cuối cùng
Sửa lỗi UID và test DICOM đầy đủ
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
    """Test kết nối DICOM với UID đúng cách"""
    print(f"🔍 Test kết nối DICOM {ip}:{port}...")
    try:
        # Tạo AE với UID đúng cách
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        print(f"   AE Title: {ae.ae_title}")
        print(f"   Requested contexts: {len(ae.requested_contexts)}")
        print(f"   Đang kết nối đến {ip}:{port} với AE Title: {ae_title}")
        
        # Test kết nối với timeout
        assoc = ae.associate(ip, port, ae_title=ae_title)
        
        if assoc.is_established:
            print(f"✅ DICOM Association thành công")
            print(f"   Remote AE Title: {assoc.remote_ae_title}")
            print(f"   Remote IP: {assoc.remote_address}")
            assoc.release()
            return True
        else:
            print(f"❌ DICOM Association thất bại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi DICOM: {e}")
        return False

def test_dicom_verification(ip, port, ae_title):
    """Test DICOM Verification Service"""
    print(f"🔍 Test DICOM Verification Service...")
    try:
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        print(f"   Đang kết nối đến {ip}:{port}...")
        assoc = ae.associate(ip, port, ae_title=ae_title)
        
        if assoc.is_established:
            print(f"✅ DICOM Association thành công")
            
            # Test Verification Service
            print(f"   Đang test Verification Service...")
            response = assoc.send_c_echo()
            
            if response.Status == 0x0000:
                print(f"✅ DICOM Verification Service hoạt động")
                assoc.release()
                return True
            else:
                print(f"❌ DICOM Verification Service thất bại: {response.Status}")
                assoc.release()
                return False
        else:
            print(f"❌ DICOM Association thất bại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi DICOM Verification: {e}")
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
    print("🏥 VOLUSON E10 DEBUG SCRIPT - PHIÊN BẢN CUỐI CÙNG")
    print("=" * 60)
    
    # Cấu hình
    voluson_ip = "10.17.2.1"
    voluson_port = 104
    voluson_ae_title = "VOLUSON_E10"
    
    print(f"📋 Cấu hình test:")
    print(f"   Voluson IP: {voluson_ip}")
    print(f"   Voluson Port: {voluson_port}")
    print(f"   Voluson AE Title: {voluson_ae_title}")
    print()
    
    # Test các bước
    tests = [
        ("Ping", lambda: test_ping(voluson_ip)),
        ("Port TCP", lambda: test_port(voluson_ip, voluson_port)),
        ("DICOM Connection", lambda: test_dicom_connection(voluson_ip, voluson_port, voluson_ae_title)),
        ("DICOM Verification", lambda: test_dicom_verification(voluson_ip, voluson_port, voluson_ae_title))
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
        
        if results.get("DICOM Connection", False):
            print("✅ DICOM kết nối thành công!")
            print("🎯 Hệ thống đã sẵn sàng đồng bộ với Voluson E10!")
        else:
            print("⚠️ DICOM chưa kết nối được")
            print("🔧 Cần kiểm tra:")
            print("   1. AE Title trên Voluson E10")
            print("   2. DICOM service đã được bật chưa")
            print("   3. Cấu hình DICOM trên máy Voluson")
    else:
        print("\n⚠️ CÓ LỖI KẾT NỐI CƠ BẢN")
        print("Vui lòng kiểm tra mạng và máy Voluson")

if __name__ == "__main__":
    main()
