@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal

REM ==========================================================
REM Local node with sync to Render (Windows)
REM Edit the 2 values below before first run.
REM ==========================================================
set "SYNC_REMOTE_URL=https://phusandaianh.io.vn"
set "SYNC_TOKEN=phongkham_2026_secure_sync"
set "SYNC_PEER_APPOINTMENTS_URL=https://phusandaianh.io.vn"
set "SYNC_PEER_TOKEN=phongkham_2026_secure_sync"

set "SYNC_ROLE=local"
set "PORT=5000"
set "FLASK_ENV=production"
set "USE_HTTPS=0"

echo.
echo [SYNC] Starting LOCAL node with:
echo        SYNC_ROLE=%SYNC_ROLE%
echo        SYNC_REMOTE_URL=%SYNC_REMOTE_URL%
echo        SYNC_PEER_APPOINTMENTS_URL=%SYNC_PEER_APPOINTMENTS_URL%
echo        PORT=%PORT%
echo        USE_HTTPS=%USE_HTTPS%
echo.
echo [NOTE] This window must stay open while syncing.
echo.

python run_waitress.py

endlocal
