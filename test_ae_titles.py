#!/usr/bin/env python3
"""
Script kiểm tra cấu hình DICOM và thử nhiều AE Title
"""

import socket
import subprocess
import sys

def test_connection():
    """Test cơ bản"""
    print("🔍 Test Ping...")
    result = subprocess.run(['ping', '-n', '1', '10.17.2.1'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Ping thành công")
    else:
        print("❌ Ping thất bại")
        return False
    
    print("\n🔍 Test Port...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(('10.17.2.1', 104))
    sock.close()
    if result == 0:
        print("✅ Port 104 mở")
    else:
        print("❌ Port 104 đóng")
        return False
    
    return True

def test_ae_titles():
    """Test nhiều AE Title phổ biến"""
    print("\n🔍 Test các AE Title phổ biến...")
    
    # Danh sách AE Title phổ biến cho GE Voluson
    ae_titles = [
        'VOLUSON_E10',
        'GE_VOLUSON',
        'VOLUSON',
        'GE',
        'DICOM', 
        'WORKLIST',
        'ECHO',
        'US',
        ''
    ]
    
    from pynetdicom import AE, VerificationPresentationContexts
    
    for ae_title in ae_titles:
        print(f"\n🔍 Thử AE Title: '{ae_title if ae_title else '(để trống)'}'...")
        try:
            ae = AE(ae_title='CLINIC_SYSTEM')
            ae.add_requested_context(VerificationPresentationContexts)
            
            assoc = ae.associate('10.17.2.1', 104, ae_title=ae_title)
            
            if assoc.is_established:
                print(f"✅ THÀNH CÔNG với AE Title: '{ae_title}'")
                print(f"   Remote AE Title: {assoc.remote_ae_title}")
                assoc.release()
                return ae_title
            else:
                print(f"❌ Thất bại")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    return None

if __name__ == "__main__":
    print("🏥 KIỂM TRA CẤU HÌNH VOLUSON E10")
    print("=" * 60)
    
    if not test_connection():
        print("\n⚠️ Kết nối cơ bản thất bại")
        sys.exit(1)
    
    correct_ae = test_ae_titles()
    
    print("\n" + "=" * 60)
    if correct_ae:
        print(f"✅ Tìm thấy AE Title đúng: '{correct_ae}'")
        print("\n🔧 Hãy cập nhật voluson_config.json với AE Title này!")
    else:
        print("❌ Không tìm thấy AE Title đúng")
        print("\n🔧 Cần kiểm tra:")
        print("   1. DICOM service đã được bật trên máy Voluson chưa?")
        print("   2. AE Title trên máy Voluson là gì?")
        print("   3. Có thể chụp ảnh màn hình cấu hình DICOM không?")
    
    sys.exit(0 if correct_ae else 1)
