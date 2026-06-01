<#
[LEGACY] Script cu — chuyen sang install_dicom_autostart_task.ps1
#>
$here = $PSScriptRoot
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here "install_dicom_autostart_task.ps1") @args
