#!/usr/bin/env python3
"""
Script debug DICOM đơn giản nhất
Test kết nối DICOM cơ bản
"""

import socket
import subprocess
import sys
import time

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

def test_dicom_simple():
    """Test DICOM đơn giản nhất"""
    print(f"🔍 Test DICOM đơn giản...")
    try:
        # Import pynetdicom
        from pynetdicom import AE, VerificationPresentationContexts
        
        print(f"   ✅ pynetdicom import thành công")
        
        # Tạo AE đơn giản
        ae = AE(ae_title='CLINIC_SYSTEM')
        print(f"   ✅ AE tạo thành công: {ae.ae_title}")
        
        # Thêm context
        ae.add_requested_context(VerificationPresentationContexts)
        print(f"   ✅ Context thêm thành công: {len(ae.requested_contexts)}")
        
        # Test kết nối
        print(f"   Đang kết nối đến 10.17.2.1:104...")
        assoc = ae.associate('10.17.2.1', 104, ae_title='VOLUSON_E10')
        
        if assoc.is_established:
            print(f"✅ DICOM kết nối thành công!")
            print(f"   Remote AE Title: {assoc.remote_ae_title}")
            print(f"   Remote IP: {assoc.remote_address}")
            assoc.release()
            return True
        else:
            print(f"❌ DICOM kết nối thất bại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi DICOM: {e}")
        print(f"   Chi tiết lỗi: {type(e).__name__}")
        return False

def test_dicom_verification():
    """Test DICOM Verification Service"""
    print(f"🔍 Test DICOM Verification Service...")
    try:
        from pynetdicom import AE, VerificationPresentationContexts
        
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        print(f"   Đang kết nối đến 10.17.2.1:104...")
        assoc = ae.associate('10.17.2.1', 104, ae_title='VOLUSON_E10')
        
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
        print(f"   Chi tiết lỗi: {type(e).__name__}")
        return False

def main():
    """Hàm chính"""
    print("🏥 VOLUSON E10 DEBUG SCRIPT - PHIÊN BẢN ĐƠN GIẢN")
    print("=" * 60)
    
    # Test các bước
    tests = [
        ("Ping", lambda: test_ping("10.17.2.1")),
        ("Port TCP", lambda: test_port("10.17.2.1", 104)),
        ("DICOM Simple", lambda: test_dicom_simple()),
        ("DICOM Verification", lambda: test_dicom_verification())
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
        
        if results.get("DICOM Simple", False):
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
