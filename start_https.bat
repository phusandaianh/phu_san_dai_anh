@echo off
chcp 65001 >nul
cd /d "%~dp0"
set USE_HTTPS=1
echo Mo: https://127.0.0.1:5000/  hoac  https://192.168.1.230:5000/
echo (Trinh duyet se canh bao cert tu ky - chap nhan / Advanced.)
python app.py
pause
