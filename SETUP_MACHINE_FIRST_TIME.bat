@echo off
cd /d "%~dp0"
echo [SETUP] Chay lan dau, can Run as Administrator...
powershell -ExecutionPolicy Bypass -File ".\scripts\setup_machine_network.ps1"
pause
