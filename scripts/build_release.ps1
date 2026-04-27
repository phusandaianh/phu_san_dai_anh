param(
    [string]$Version,
    [string]$ConfigPath = ".\update\update-config.json"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ConfigPath)) {
    throw "Khong tim thay file cau hinh: $ConfigPath"
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $Version -or $Version.Trim() -eq "") {
    $Version = Get-Date -Format "yyyy.MM.dd.HHmm"
}

$buildRoot = Join-Path $projectRoot "build"
$releaseRoot = Join-Path $projectRoot "releases"
$stagingDir = Join-Path $buildRoot "staging_$Version"
$zipName = "clinic-app-$Version.zip"
$zipPath = Join-Path $releaseRoot $zipName

if (Test-Path $stagingDir) { Remove-Item $stagingDir -Recurse -Force }
New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null

$excludeDirs = @(
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "build", "releases", "node_modules", ".cursor"
)

$excludeFiles = @(
    "*.log", "*.tmp", "*.bak", "clinic.db-shm", "clinic.db-wal", "mwl.db-shm", "mwl.db-wal"
)

Write-Host "[BUILD] Dang sao chep source vao staging..."
Get-ChildItem -Path $projectRoot -Force | ForEach-Object {
    $name = $_.Name
    if ($excludeDirs -contains $name) { return }
    $dest = Join-Path $stagingDir $name
    Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
}

foreach ($pattern in $excludeFiles) {
    Get-ChildItem -Path $stagingDir -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}

$releaseInfo = [ordered]@{
    version = $Version
    built_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    entrypoint = "run_local_sync.bat"
}
$releaseInfo | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $stagingDir "release-info.json") -Encoding UTF8

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Write-Host "[BUILD] Dang dong goi: $zipPath"
Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -Force

Remove-Item $stagingDir -Recurse -Force

Write-Host "[DONE] Build thanh cong:"
Write-Host "       Version: $Version"
Write-Host "       File:    $zipPath"
