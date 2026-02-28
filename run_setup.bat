@echo off
REM Run PowerShell script as Administrator

powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-ExecutionPolicy Bypass', '-File setup_mwl_service_simple.ps1' -Verb RunAs"
pause
