@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

REM Khớp Render: phong-kham-booking (SYNC_TOKEN phải giống nhau)
set "SYNC_REMOTE_URL=https://booking.phusandaianh.io.vn"
set "SYNC_TOKEN=PKDA_SYNC_2026"
set "SYNC_PEER_APPOINTMENTS_URL=https://booking.phusandaianh.io.vn"
set "SYNC_PEER_TOKEN=PKDA_SYNC_2026"

set "SYNC_ROLE=local"
set "PORT=5000"
set "FLASK_ENV=production"
set "SECRET_KEY=PKDA_LOCAL_2026_CHANGE_ME_9f3b7a"
set "USE_HTTPS=0"

echo.
echo [SYNC] Starting LOCAL node with:
echo        SYNC_ROLE=%SYNC_ROLE%
echo        SYNC_REMOTE_URL=%SYNC_REMOTE_URL%
echo        SYNC_TOKEN=%SYNC_TOKEN%
echo        PORT=%PORT%
echo.
echo [NOTE] Giữ cửa sổ mở. PowerShell: .\run_local_sync.bat
echo.

python run_waitress.py

endlocal
