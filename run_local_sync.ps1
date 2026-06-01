# Chạy node local có đồng bộ lên cloud (PowerShell)
# Cách dùng: .\run_local_sync.ps1

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$env:SYNC_REMOTE_URL = 'https://booking.phusandaianh.io.vn'
$env:SYNC_TOKEN = 'PKDA_SYNC_2026'
$env:SYNC_PEER_APPOINTMENTS_URL = 'https://booking.phusandaianh.io.vn'
$env:SYNC_PEER_TOKEN = 'PKDA_SYNC_2026'
$env:SYNC_ROLE = 'local'
$env:PORT = '5000'
$env:FLASK_ENV = 'production'
$env:USE_HTTPS = '0'

Write-Host ''
Write-Host '[SYNC] Starting LOCAL node with:'
Write-Host "       SYNC_ROLE=$($env:SYNC_ROLE)"
Write-Host "       SYNC_REMOTE_URL=$($env:SYNC_REMOTE_URL)"
Write-Host "       SYNC_TOKEN=$($env:SYNC_TOKEN)"
Write-Host "       PORT=$($env:PORT)"
Write-Host ''
Write-Host '[NOTE] Giữ cửa sổ này mở để đồng bộ lịch lên cloud.'
Write-Host ''

python run_waitress.py
