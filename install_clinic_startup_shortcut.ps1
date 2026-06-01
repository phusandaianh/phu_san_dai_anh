<#
Tao shortcut trong Startup (khong can Admin).
Chay: powershell -ExecutionPolicy Bypass -File .\install_clinic_startup_shortcut.ps1
#>

$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot
$Launcher = Join-Path $ProjectDir "scripts\clinic_autostart_launcher.ps1"
$StartupDir = [Environment]::GetFolderPath("Startup")
$LinkPath = Join-Path $StartupDir "Phong Kham Dai Anh.lnk"

if (-not (Test-Path $Launcher)) {
    throw "Khong tim thay: $Launcher"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($LinkPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Launcher`""
$shortcut.WorkingDirectory = $ProjectDir
$shortcut.Description = "Khoi dong http://127.0.0.1:5000/ khi dang nhap Windows"
$shortcut.Save()

Write-Host "Da tao shortcut Startup:" -ForegroundColor Green
Write-Host "  $LinkPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Go bo: xoa file shortcut tren trong Startup (Win+R -> shell:startup)" -ForegroundColor Yellow
