@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================================
echo  CAI DAT TU KHOI DONG DICOM / WORKLIST (MAY SIÊU ÂM)
echo  - Worklist MWL     : port 104  (CLINIC_SYSTEM)
echo  - Nhan hinh C-STORE: port 11112 (AE: PC)
echo  - Orthanc PACS     : port 4242 (neu da cai)
echo ========================================================
echo.
echo Can quyen Administrator (UAC).
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0install_dicom_autostart_task.ps1\"\" -RunNow'"
pause
