@echo off
chcp 65001 >nul
setlocal

REM ==========================================================
REM Local node with sync to Render (Windows)
REM Edit the 2 values below before first run.
REM ==========================================================
set "SYNC_REMOTE_URL=https://your-app.onrender.com"
set "SYNC_TOKEN=REPLACE_WITH_A_STRONG_SHARED_SECRET"

set "SYNC_ROLE=local"
set "PORT=5000"
set "FLASK_ENV=production"

echo.
echo [SYNC] Starting LOCAL node with:
echo        SYNC_ROLE=%SYNC_ROLE%
echo        SYNC_REMOTE_URL=%SYNC_REMOTE_URL%
echo        PORT=%PORT%
echo.
echo [NOTE] This window must stay open while syncing.
echo.

python run_waitress.py

endlocal
