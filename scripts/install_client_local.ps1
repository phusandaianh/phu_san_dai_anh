param(
    [string]$AppRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $AppRoot -or $AppRoot.Trim() -eq "") {
    $AppRoot = Split-Path -Parent $PSScriptRoot
}

Write-Host "========================================================"
Write-Host " CAU HINH CLIENT LOCAL"
Write-Host "========================================================"
Write-Host " AppRoot: $AppRoot"
Write-Host ""

$setupScript = Join-Path $AppRoot "scripts\setup_machine_network.ps1"
$shortcutScript = Join-Path $AppRoot "scripts\create_desktop_shortcuts.ps1"

if (-not (Test-Path $setupScript)) {
    throw "Khong tim thay $setupScript"
}
if (-not (Test-Path $shortcutScript)) {
    throw "Khong tim thay $shortcutScript"
}

Write-Host "[1/2] Setup hosts (can quyen admin)..."
& powershell -ExecutionPolicy Bypass -File $setupScript

Write-Host "[2/2] Tao shortcut desktop..."
& powershell -ExecutionPolicy Bypass -File $shortcutScript -AppRoot $AppRoot

Write-Host ""
Write-Host "[DONE] May da san sang. Hay mo shortcut 'Mo Phong Kham'."
