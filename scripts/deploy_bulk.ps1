param(
    [string]$CsvPath = ".\deployment\machines.csv",
    [string]$TemplateConfigPath = ".\deployment\machine-config.example.json",
    [switch]$SkipCopy
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$fullCsvPath = if ([System.IO.Path]::IsPathRooted($CsvPath)) { $CsvPath } else { Join-Path $projectRoot $CsvPath }
$fullTemplatePath = if ([System.IO.Path]::IsPathRooted($TemplateConfigPath)) { $TemplateConfigPath } else { Join-Path $projectRoot $TemplateConfigPath }

if (-not (Test-Path $fullCsvPath)) { throw "Khong tim thay CSV: $fullCsvPath" }
if (-not (Test-Path $fullTemplatePath)) { throw "Khong tim thay template config: $fullTemplatePath" }

$template = Get-Content $fullTemplatePath -Raw | ConvertFrom-Json
$rows = Import-Csv -Path $fullCsvPath
if (-not $rows -or $rows.Count -eq 0) { throw "CSV rong: $fullCsvPath" }

$excludeDirs = @(".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".cursor", "build", "releases")
$excludeFiles = @("*.log", "*.tmp", "*.bak", "clinic.db-shm", "clinic.db-wal", "mwl.db-shm", "mwl.db-wal")

function Copy-ProjectToTarget {
    param([string]$TargetPath)
    New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
    Get-ChildItem -Path $projectRoot -Force | ForEach-Object {
        if ($excludeDirs -contains $_.Name) { return }
        Copy-Item -Path $_.FullName -Destination (Join-Path $TargetPath $_.Name) -Recurse -Force
    }
    foreach ($pattern in $excludeFiles) {
        Get-ChildItem -Path $TargetPath -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    }
}

foreach ($row in $rows) {
    $machine = ($row.machine_name | Out-String).Trim()
    $target = ($row.target_path | Out-String).Trim()
    if (-not $machine -or -not $target) {
        Write-Warning "Bo qua dong CSV thieu machine_name/target_path"
        continue
    }

    Write-Host "========================================================"
    Write-Host "[DEPLOY] $machine -> $target"
    Write-Host "========================================================"

    if (-not $SkipCopy) {
        Copy-ProjectToTarget -TargetPath $target
    } else {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }

    $cfg = $template | ConvertTo-Json -Depth 8 | ConvertFrom-Json
    $cfg.machine_name = $machine
    if ($row.app_port) { $cfg.app_port = [int]$row.app_port }
    if ($row.server_hostname) { $cfg.network.server_hostname = $row.server_hostname }
    if ($row.server_ip) { $cfg.network.server_ip = $row.server_ip }
    if ($row.sync_remote_url) { $cfg.sync.remote_url = $row.sync_remote_url }
    if ($row.sync_token) {
        $cfg.sync.token = $row.sync_token
        $cfg.sync.peer_token = $row.sync_token
    }
    $cfg.sync.peer_appointments_url = $cfg.sync.remote_url

    $deployConfigPath = Join-Path $target "deployment\machine-config.json"
    New-Item -ItemType Directory -Path (Split-Path -Parent $deployConfigPath) -Force | Out-Null
    $cfg | ConvertTo-Json -Depth 8 | Set-Content -Path $deployConfigPath -Encoding UTF8

    $installCmd = @"
@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File ".\scripts\install_client_local.ps1" -AppRoot "%~dp0"
pause
"@
    Set-Content -Path (Join-Path $target "INSTALL_CLIENT_LOCAL.bat") -Value $installCmd -Encoding ASCII

    Write-Host "[OK] Da tao machine-config va script install cho $machine"
    Write-Host "     Tren may $machine, chay INSTALL_CLIENT_LOCAL.bat bang quyen admin."
}

Write-Host ""
Write-Host "[DONE] Bulk deploy hoan tat."
