@echo off
setlocal
cd /d "%~dp0"

echo [SERVICE] Starting resilient local sync loop...

:loop
echo.
echo [SERVICE] Launching run_local_sync.bat at %date% %time%
call "%~dp0run_local_sync.bat"
echo [SERVICE] Process exited with code %errorlevel% at %date% %time%
echo [SERVICE] Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop

