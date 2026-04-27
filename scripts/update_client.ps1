param(
    [string]$ConfigPath = ".\update\update-config.json",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ConfigPath)) {
    throw "Khong tim thay file cau hinh: $ConfigPath"
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$appRoot = if ($config.client_app_root) { $config.client_app_root } else { Split-Path -Parent $PSScriptRoot }
$workDir = if ($config.client_work_dir) { $config.client_work_dir } else { Join-Path $env:ProgramData "PhongKhamDaiAnh\updater" }
$latestUrl = "$($config.public_base_url.TrimEnd('/'))/latest.json"

New-Item -ItemType Directory -Path $workDir -Force | Out-Null
$latestPath = Join-Path $workDir "latest.json"

Write-Host "[UPDATE] Kiem tra phien ban moi tu $latestUrl"
Invoke-WebRequest -Uri $latestUrl -OutFile $latestPath -UseBasicParsing
$latest = Get-Content $latestPath -Raw | ConvertFrom-Json

$localInfoPath = Join-Path $appRoot "release-info.json"
$currentVersion = ""
if (Test-Path $localInfoPath) {
    try {
        $currentInfo = Get-Content $localInfoPath -Raw | ConvertFrom-Json
        $currentVersion = ($currentInfo.version | Out-String).Trim()
    } catch {}
}

$targetVersion = ($latest.version | Out-String).Trim()
if (-not $Force -and $currentVersion -eq $targetVersion) {
    Write-Host "[UPDATE] Da o ban moi nhat: $currentVersion"
    exit 0
}

$packageUrl = ($latest.package_url | Out-String).Trim()
if (-not $packageUrl) {
    throw "latest.json khong co package_url"
}

$zipPath = Join-Path $workDir $latest.package
$extractDir = Join-Path $workDir "extract_$targetVersion"
$backupDir = Join-Path $workDir "backup_$((Get-Date).ToString('yyyyMMdd_HHmmss'))"

Write-Host "[UPDATE] Tai goi: $packageUrl"
Invoke-WebRequest -Uri $packageUrl -OutFile $zipPath -UseBasicParsing

if ($latest.sha256) {
    $actualHash = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToLower()
    if ($actualHash -ne ($latest.sha256.ToLower())) {
        throw "SHA256 khong khop. expected=$($latest.sha256) actual=$actualHash"
    }
}

if (Test-Path $extractDir) { Remove-Item $extractDir -Recurse -Force }
New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

Write-Host "[UPDATE] Tao backup: $backupDir"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Get-ChildItem -Path $appRoot -Force | ForEach-Object {
    $name = $_.Name
    if ($name -in @("clinic.db", "mwl.db", "uploads", "backups", "ssl", "venv", ".venv")) { return }
    Copy-Item -Path $_.FullName -Destination (Join-Path $backupDir $name) -Recurse -Force
}

Write-Host "[UPDATE] Cap nhat file app..."
Get-ChildItem -Path $extractDir -Force | ForEach-Object {
    $name = $_.Name
    if ($name -in @("clinic.db", "mwl.db")) { return }
    Copy-Item -Path $_.FullName -Destination (Join-Path $appRoot $name) -Recurse -Force
}

Write-Host "[DONE] Da cap nhat len ban $targetVersion"
Write-Host "       Backup tai: $backupDir"
