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
    throw "Vui long truyen -Version. Vi du: -Version 2026.04.27.1"
}

$zipName = "clinic-app-$Version.zip"
$zipPath = Join-Path (Join-Path $projectRoot "releases") $zipName
if (-not (Test-Path $zipPath)) {
    throw "Khong tim thay goi release: $zipPath. Hay chay build truoc."
}

$publishPath = $config.publish_share
if (-not $publishPath) {
    throw "Thieu publish_share trong update-config.json"
}

New-Item -ItemType Directory -Path $publishPath -Force | Out-Null

$publishedZipPath = Join-Path $publishPath $zipName
Copy-Item -Path $zipPath -Destination $publishedZipPath -Force

$latest = [ordered]@{
    version = $Version
    package = $zipName
    package_url = "$($config.public_base_url.TrimEnd('/'))/$zipName"
    sha256 = (Get-FileHash -Path $zipPath -Algorithm SHA256).Hash.ToLower()
    published_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    min_updater_version = "1.0.0"
    notes = "Auto published from publish_release.ps1"
}

$latestPath = Join-Path $publishPath "latest.json"
$latest | ConvertTo-Json -Depth 5 | Set-Content -Path $latestPath -Encoding UTF8

Write-Host "[DONE] Publish thanh cong"
Write-Host "       Version: $Version"
Write-Host "       Package: $publishedZipPath"
Write-Host "       Latest:  $latestPath"
