param(
    [string]$ConfigPath = ".\deployment\machine-config.json"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$fullConfigPath = if ([System.IO.Path]::IsPathRooted($ConfigPath)) { $ConfigPath } else { Join-Path $projectRoot $ConfigPath }

if (-not (Test-Path $fullConfigPath)) {
    throw "Khong tim thay file cau hinh may: $fullConfigPath"
}

$cfg = Get-Content $fullConfigPath -Raw | ConvertFrom-Json

$env:SYNC_ROLE = ($cfg.sync.role | Out-String).Trim()
$env:SYNC_REMOTE_URL = ($cfg.sync.remote_url | Out-String).Trim()
$env:SYNC_TOKEN = ($cfg.sync.token | Out-String).Trim()
$env:SYNC_PEER_APPOINTMENTS_URL = ($cfg.sync.peer_appointments_url | Out-String).Trim()
$env:SYNC_PEER_TOKEN = ($cfg.sync.peer_token | Out-String).Trim()
$env:PORT = [string]($cfg.app_port)
$env:FLASK_ENV = "production"
$env:USE_HTTPS = if ($cfg.use_https) { "1" } else { "0" }

Write-Host "========================================================"
Write-Host " KHOI DONG NODE PHONG KHAM (LOCAL MODE)"
Write-Host "========================================================"
Write-Host " Machine: $($cfg.machine_name)"
Write-Host " Port:    $($env:PORT)"
Write-Host " URL:     http://127.0.0.1:$($env:PORT)/"
Write-Host " Sync:    $($env:SYNC_REMOTE_URL)"
Write-Host "========================================================"
Write-Host ""

Push-Location $projectRoot
try {
    python run_waitress.py
}
finally {
    Pop-Location
}
