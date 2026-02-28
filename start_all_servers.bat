@echo off
chcp 65001 >nul
echo ========================================================================
echo KHỞI ĐỘNG TẤT CẢ SERVERS - PHÒNG KHÁM ĐẠI ANH
echo ========================================================================
echo.
echo Cần chạy 2 terminals riêng biệt:
echo 1. Terminal này: Web Server (app.py)
echo 2. Terminal khác: DICOM MWL Server (dicom_mwl_server.py)
echo.
echo ========================================================================
echo.

:: Chạy Web Server (REST API)
echo Đang khởi động Web Server (port 5000)...
start "Web Server - Port 5000" cmd /k "python run.py"

:: Đợi 3 giây
timeout /t 3 /nobreak >nul

:: Chạy DICOM MWL Server
echo Đang khởi động DICOM MWL Server (port 104)...
start "DICOM MWL Server - Port 104" cmd /k "python dicom_mwl_server.py"

echo.
echo ========================================================================
echo ĐÃ KHỞI ĐỘNG CẢ 2 SERVERS!
echo ========================================================================
echo.
echo Web Server: https://127.0.0.1:5000/ (hoặc https://IP_máy_chủ:5000)
echo DICOM MWL Server: 0.0.0.0:104 (AE Title: CLINIC_SYSTEM)
echo.
echo Bây giờ bạn có thể test trên Voluson E10!
echo.
pause

