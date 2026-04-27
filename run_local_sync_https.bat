@echo off
chcp 65001 >nul
setlocal

REM ==========================================================
REM Local HTTPS node with sync to Render (Windows)
REM Edit the 2 values below before first run.
REM ==========================================================
set "SYNC_REMOTE_URL=https://phu-san-dai-anh.onrender.com/"
set "SYNC_TOKEN=phongkham_2026_secure_sync"
set "SYNC_PEER_APPOINTMENTS_URL=https://phusandaianh.io.vn"
set "SYNC_PEER_TOKEN=phongkham_2026_secure_sync"

set "SYNC_ROLE=local"
set "PORT=5000"
set "FLASK_ENV=production"
set "USE_HTTPS=1"
set "SSL_CERT=ssl\dev.crt"
set "SSL_KEY=ssl\dev.key"

if not exist ssl mkdir ssl

if not exist "%SSL_CERT%" (
  echo [HTTPS] Missing certificate. Generating self-signed cert...
  python generate_dev_ssl.py
)

if not exist "%SSL_CERT%" (
  echo [ERROR] Cannot find %SSL_CERT%
  pause
  exit /b 1
)

if not exist "%SSL_KEY%" (
  echo [ERROR] Cannot find %SSL_KEY%
  pause
  exit /b 1
)

echo.
echo [SYNC+HTTPS] Starting LOCAL node with:
echo             SYNC_ROLE=%SYNC_ROLE%
echo             SYNC_REMOTE_URL=%SYNC_REMOTE_URL%
echo             SYNC_PEER_APPOINTMENTS_URL=%SYNC_PEER_APPOINTMENTS_URL%
echo             PORT=%PORT%
echo             USE_HTTPS=%USE_HTTPS%
echo.
echo [URL] https://0.0.0.0:%PORT%/
echo [NOTE] Install/trust ssl\dev.crt on LAN devices to avoid browser warning.
echo.

python run_waitress.py

endlocal
