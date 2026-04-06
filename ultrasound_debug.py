#!/usr/bin/env python3
"""
Script debug kết nối máy siêu âm
Kiểm tra chi tiết các vấn đề kết nối
"""

import socket
import subprocess
import sys
import time
from pynetdicom import AE, VerificationPresentationContexts
import pydicom

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
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        print(f"   Đang kết nối đến {ip}:{port} với AE Title: {ae_title}")
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

def check_network_config():
    """Kiểm tra cấu hình mạng"""
    print("🔍 Kiểm tra cấu hình mạng...")
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        print("📋 Cấu hình mạng hiện tại:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Lỗi kiểm tra mạng: {e}")

def check_firewall():
    """Kiểm tra firewall"""
    print("🔍 Kiểm tra Windows Firewall...")
    try:
        result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], 
                              capture_output=True, text=True)
        print("📋 Trạng thái Firewall:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Lỗi kiểm tra firewall: {e}")

def main():
    """Hàm chính"""
    print("🏥 ULTRASOUND DEBUG SCRIPT")
    print("=" * 50)
    
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
        ("DICOM Connection", lambda: test_dicom_connection(ultrasound_ip, ultrasound_port, ultrasound_ae_title))
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
    
    # Kiểm tra cấu hình mạng
    print(f"\n{'='*20} Network Config {'='*20}")
    check_network_config()
    
    print(f"\n{'='*20} Firewall Status {'='*20}")
    check_firewall()
    
    # Tổng kết
    print(f"\n{'='*50}")
    print("📊 TỔNG KẾT DEBUG")
    print(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nKết quả: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TẤT CẢ TEST THÀNH CÔNG!")
        print("Kết nối máy siêu âm hoạt động bình thường.")
    else:
        print("\n⚠️ CÓ LỖI KẾT NỐI")
        print("\n🔧 Gợi ý khắc phục:")
        
        if not results.get("Ping", True):
            print("1. Kiểm tra máy siêu âm có bật không")
            print("2. Kiểm tra cáp mạng")
            print("3. Kiểm tra IP có đúng không")
        
        if not results.get("Port TCP", True):
            print("4. Kiểm tra port 104 có mở không")
            print("5. Kiểm tra firewall")
            print("6. Kiểm tra DICOM service trên máy siêu âm")
        
        if not results.get("DICOM Connection", True):
            print("7. Kiểm tra AE Title có khớp không")
            print("8. Kiểm tra DICOM configuration trên máy siêu âm")
            print("9. Kiểm tra network routing")

if __name__ == "__main__":
    main()
