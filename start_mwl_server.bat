@echo off
REM MWL Server Auto-Start Batch Script
REM Run as Administrator required

SETLOCAL ENABLEDELAYEDEXPANSION

REM Project directory
SET PROJECT_DIR=J:\DU_AN_AI\Phong_kham_dai_anh

REM Change to project directory
cd /d %PROJECT_DIR%

REM Log file
SET LOG_FILE=%PROJECT_DIR%\mwl_server.log

:start_server
REM Add timestamp to log
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)

echo [%mydate% %mytime%] Starting MWL Server... >> %LOG_FILE%

REM Run MWL Server
python mwl_server.py >> %LOG_FILE% 2>&1

REM If server stops/crashes, log it and restart after 10 seconds
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)

echo [%mydate% %mytime%] MWL Server stopped. Restarting in 10 seconds... >> %LOG_FILE%

REM Wait 10 seconds before restarting
timeout /t 10 /nobreak

REM Restart server
goto start_server

ENDLOCAL
