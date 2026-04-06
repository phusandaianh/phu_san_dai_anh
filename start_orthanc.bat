@echo off
setlocal
cd /d "%~dp0"

if not exist "orthanc\bin\Orthanc.exe" (
  echo [ERROR] Khong tim thay orthanc\bin\Orthanc.exe
  pause
  exit /b 1
)

if not exist "orthanc\orthanc.json" (
  echo [ERROR] Khong tim thay orthanc\orthanc.json
  pause
  exit /b 1
)

echo [INFO] Starting Orthanc PACS...
echo [INFO] DICOM AE: CLINIC_PACS
echo [INFO] DICOM Port: 4242
echo [INFO] Web: http://127.0.0.1:8042
echo.
"orthanc\bin\Orthanc.exe" "orthanc\orthanc.json"

endlocal
