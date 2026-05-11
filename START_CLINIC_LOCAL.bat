@echo off
cd /d "%~dp0"
echo [CLINIC] Khoi dong node local 127.0.0.1...
powershell -ExecutionPolicy Bypass -File ".\scripts\start_clinic_node.ps1"
pause
