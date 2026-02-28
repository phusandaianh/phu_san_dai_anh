@echo off
echo ========================================
echo    VOLUSON E10 AUTO SETUP SCRIPT
echo ========================================
echo.

REM Kiểm tra quyền Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Đang chạy với quyền Administrator
) else (
    echo ❌ Cần quyền Administrator để chạy script này
    echo Vui lòng chạy lại với quyền Administrator
    pause
    exit /b 1
)

echo.
echo 🔍 Kiểm tra Python...
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Python đã được cài đặt
    python --version
) else (
    echo ❌ Python chưa được cài đặt
    echo Vui lòng cài đặt Python 3.8+ từ https://python.org
    pause
    exit /b 1
)

echo.
echo 📦 Cài đặt các package cần thiết...
pip install pydicom==2.3.0
pip install pynetdicom==2.0.0
pip install flask==2.0.1
pip install flask-sqlalchemy==2.5.1

echo.
echo 🔧 Cấu hình Windows Firewall...
netsh advfirewall firewall add rule name="Voluson DICOM" dir=in action=allow protocol=TCP localport=104
netsh advfirewall firewall add rule name="Voluson DICOM Out" dir=out action=allow protocol=TCP remoteport=104

echo.
echo 📝 Tạo file cấu hình...
echo {> voluson_config.json
echo   "sync_enabled": true,>> voluson_config.json
echo   "voluson_ip": "10.17.2.1",>> voluson_config.json
echo   "voluson_port": 104,>> voluson_config.json
echo   "ae_title": "CLINIC_SYSTEM",>> voluson_config.json
echo   "voluson_ae_title": "VOLUSON_E10",>> voluson_config.json
echo   "sync_interval": 30,>> voluson_config.json
echo   "retry_attempts": 3,>> voluson_config.json
echo   "retry_delay": 10,>> voluson_config.json
echo   "log_level": "INFO">> voluson_config.json
echo }>> voluson_config.json

echo.
echo 🌐 Kiểm tra kết nối mạng...
ping -n 1 10.17.2.1 >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Có thể kết nối đến máy Voluson E10
) else (
    echo ⚠️ Không thể kết nối đến máy Voluson E10
    echo Vui lòng kiểm tra:
    echo - IP máy Voluson có đúng không
    echo - Máy Voluson có bật không
    echo - Cáp mạng có kết nối không
)

echo.
echo 🧪 Test import thư viện DICOM...
python -c "import pydicom, pynetdicom; print('✅ DICOM libraries OK')" 2>nul
if %errorLevel% == 0 (
    echo ✅ DICOM libraries hoạt động tốt
) else (
    echo ❌ Lỗi import DICOM libraries
    echo Vui lòng chạy lại: pip install pydicom pynetdicom
)

echo.
echo 📊 Tạo báo cáo cài đặt...
echo Cài đặt hoàn thành lúc: %date% %time% > setup_report.txt
echo Python version: >> setup_report.txt
python --version >> setup_report.txt
echo. >> setup_report.txt
echo Packages installed: >> setup_report.txt
pip list | findstr "pydicom pynetdicom flask" >> setup_report.txt

echo.
echo ========================================
echo           CÀI ĐẶT HOÀN THÀNH
echo ========================================
echo.
echo ✅ Các bước đã hoàn thành:
echo    - Python packages đã cài đặt
echo    - Windows Firewall đã cấu hình
echo    - File cấu hình đã tạo
echo    - Kết nối mạng đã kiểm tra
echo.
echo 📋 Bước tiếp theo:
echo    1. Cấu hình máy Voluson E10 (xem VOLUSON_MACHINE_SETUP.md)
echo    2. Khởi động ứng dụng: python app.py
echo    3. Truy cập: http://127.0.0.1:5000/examination-list.html
echo    4. Cấu hình trong tab 'Voluson'
echo.
echo 📖 Tài liệu:
echo    - VOLUSON_SETUP_GUIDE.md: Hướng dẫn chi tiết
echo    - VOLUSON_MACHINE_SETUP.md: Cấu hình máy Voluson
echo    - setup_report.txt: Báo cáo cài đặt
echo.
pause
