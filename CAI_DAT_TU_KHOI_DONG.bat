@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================================
echo  CAI DAT TU KHOI DONG - PHONG KHAM DAI ANH
echo  (Server http://127.0.0.1:5000/ + mo trinh duyet khi dang nhap)
echo ========================================================
echo.
echo Can quyen Administrator. Neu hien UAC, bam Yes.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0install_clinic_autostart_task.ps1\"\" -RunNow'"
pause
