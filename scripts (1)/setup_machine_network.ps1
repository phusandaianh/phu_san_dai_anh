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
$hostName = ($cfg.network.server_hostname | Out-String).Trim()
$hostIp = ($cfg.network.server_ip | Out-String).Trim()

if (-not $hostName -or -not $hostIp) {
    throw "Thieu network.server_hostname hoac network.server_ip trong cau hinh"
}

$hostsPath = "$env:WINDIR\System32\drivers\etc\hosts"
$entry = "$hostIp`t$hostName"

Write-Host "[SETUP] Cap nhat hosts: $entry"

$hostsRaw = Get-Content $hostsPath -Raw
$pattern = "(?im)^\s*\d{1,3}(?:\.\d{1,3}){3}\s+$([regex]::Escape($hostName))\s*$"
if ($hostsRaw -match $pattern) {
    $hostsRaw = [regex]::Replace($hostsRaw, $pattern, $entry)
} else {
    if (-not $hostsRaw.EndsWith("`r`n")) { $hostsRaw += "`r`n" }
    $hostsRaw += "$entry`r`n"
}

Set-Content -Path $hostsPath -Value $hostsRaw -Encoding ASCII
Write-Host "[DONE] Da cap nhat hosts. Bay gio co the dung URL hostname co dinh."
