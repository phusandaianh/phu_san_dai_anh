@echo off
chcp 65001 >nul
cd /d "%~dp0"
set USE_HTTPS=1
echo HTTPS (Werkzeug threaded + SSL). Can: pip install waitress
echo Mo: https://127.0.0.1:5000/
python run_waitress.py
pause
