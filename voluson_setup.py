#!/usr/bin/env python3
"""
Script tự động kiểm tra và cài đặt đồng bộ máy siêu âm
Chạy script này để kiểm tra tất cả các yêu cầu và cài đặt tự động
"""

import subprocess
import sys
import os
import json
import socket
import time
from pathlib import Path

def check_python_version():
    """Kiểm tra phiên bản Python"""
    print("🔍 Kiểm tra phiên bản Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Cần Python 3.8+")
        return False

def install_packages():
    """Cài đặt các package cần thiết"""
    print("\n📦 Cài đặt các package cần thiết...")
    
    packages = [
        "pydicom==2.3.0",
        "pynetdicom==2.0.0", 
        "flask==2.0.1",
        "flask-sqlalchemy==2.5.1"
    ]
    
    for package in packages:
        try:
            print(f"   Cài đặt {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} - OK")
        except subprocess.CalledProcessError:
            print(f"   ❌ {package} - Lỗi cài đặt")
            return False
    
    return True

def test_dicom_imports():
    """Test import các thư viện DICOM"""
    print("\n🧪 Test import thư viện DICOM...")
    
    try:
        import pydicom
        print("   ✅ pydicom - OK")
    except ImportError:
        print("   ❌ pydicom - Lỗi import")
        return False
    
    try:
        import pynetdicom
        print("   ✅ pynetdicom - OK")
    except ImportError:
        print("   ❌ pynetdicom - Lỗi import")
        return False
    
    return True

def check_network_connectivity(ip="10.17.2.1", port=104):
    """Kiểm tra kết nối mạng đến máy siêu âm"""
    print(f"\n🌐 Kiểm tra kết nối mạng đến {ip}:{port}...")
    
    try:
        # Test ping
        result = subprocess.run(['ping', '-n', '1', ip], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ Ping {ip} - OK")
        else:
            print(f"   ❌ Ping {ip} - Không thể kết nối")
            return False
        
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ TCP {ip}:{port} - OK")
            return True
        else:
            print(f"   ❌ TCP {ip}:{port} - Port không mở")
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi kiểm tra mạng: {e}")
        return False

def create_config_file():
    """Tạo file cấu hình máy siêu âm"""
    print("\n📝 Tạo file cấu hình...")
    
    config = {
        "sync_enabled": True,
        "voluson_ip": "10.17.2.1",
        "voluson_port": 104,
        "ae_title": "CLINIC_SYSTEM",
        "voluson_ae_title": "MAY_SIEU_AM",
        "sync_interval": 30,
        "retry_attempts": 3,
        "retry_delay": 10,
        "log_level": "INFO"
    }
    
    try:
        with open('voluson_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("   ✅ voluson_config.json - Đã tạo")
        return True
    except Exception as e:
        print(f"   ❌ Lỗi tạo config: {e}")
        return False

def test_ultrasound_connection():
    """Test kết nối DICOM đến máy siêu âm"""
    print("\n🔗 Test kết nối DICOM đến máy siêu âm...")
    
    try:
        from pynetdicom import AE, VerificationPresentationContexts
        
        # Tạo AE
        ae = AE(ae_title='CLINIC_SYSTEM')
        ae.add_requested_context(VerificationPresentationContexts)
        
        # Test kết nối
        assoc = ae.associate('10.17.2.1', 104, ae_title='MAY_SIEU_AM')
        
        if assoc.is_established:
            print("   ✅ DICOM Association - Thành công")
            assoc.release()
            return True
        else:
            print("   ❌ DICOM Association - Thất bại")
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi test DICOM: {e}")
        return False

def check_database():
    """Kiểm tra database"""
    print("\n🗄️ Kiểm tra database...")
    
    if os.path.exists('clinic.db'):
        print("   ✅ clinic.db - Tồn tại")
        return True
    else:
        print("   ❌ clinic.db - Không tồn tại")
        return False

def create_setup_report():
    """Tạo báo cáo cài đặt"""
    print("\n📊 Tạo báo cáo cài đặt...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "checks": {
            "python_version": check_python_version(),
            "packages_installed": install_packages(),
            "dicom_imports": test_dicom_imports(),
            "network_connectivity": check_network_connectivity(),
            "config_file": create_config_file(),
            "dicom_connection": test_ultrasound_connection(),
            "database": check_database()
        }
    }
    
    try:
        with open('ultrasound_setup_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("   ✅ Báo cáo đã lưu: ultrasound_setup_report.json")
        return True
    except Exception as e:
        print(f"   ❌ Lỗi tạo báo cáo: {e}")
        return False

def main():
    """Hàm chính"""
    print("🏥 ULTRASOUND SETUP SCRIPT")
    print("=" * 50)
    
    # Chạy tất cả các kiểm tra
    checks = [
        ("Python Version", check_python_version),
        ("Install Packages", install_packages),
        ("DICOM Imports", test_dicom_imports),
        ("Network Connectivity", lambda: check_network_connectivity()),
        ("Config File", create_config_file),
        ("DICOM Connection", test_ultrasound_connection),
        ("Database", check_database),
        ("Setup Report", create_setup_report)
    ]
    
    results = {}
    for name, func in checks:
        try:
            results[name] = func()
        except Exception as e:
            print(f"❌ Lỗi trong {name}: {e}")
            results[name] = False
    
    # Tổng kết
    print("\n" + "=" * 50)
    print("📋 TỔNG KẾT CÀI ĐẶT")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nKết quả: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 CÀI ĐẶT THÀNH CÔNG!")
        print("Hệ thống đồng bộ máy siêu âm đã sẵn sàng.")
        print("\nBước tiếp theo:")
        print("1. Khởi động ứng dụng: python app.py")
        print("2. Truy cập: http://127.0.0.1:5000/examination-list.html")
        print("3. Cấu hình tại: http://127.0.0.1:5000/worklist-center.html")
    else:
        print("\n⚠️ CÀI ĐẶT CHƯA HOÀN THÀNH")
        print("Vui lòng kiểm tra các lỗi trên và thử lại.")
        print("\nHướng dẫn chi tiết: README_DOCUMENTATION_INDEX.md")

if __name__ == "__main__":
    main()
