param(
    [string]$AppRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $AppRoot -or $AppRoot.Trim() -eq "") {
    $AppRoot = Split-Path -Parent $PSScriptRoot
}

$desktop = [Environment]::GetFolderPath("Desktop")
$wsh = New-Object -ComObject WScript.Shell

function New-ShortcutFile {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$Arguments = "",
        [string]$WorkingDirectory = ""
    )
    $s = $wsh.CreateShortcut($ShortcutPath)
    $s.TargetPath = $TargetPath
    if ($Arguments) { $s.Arguments = $Arguments }
    if ($WorkingDirectory) { $s.WorkingDirectory = $WorkingDirectory }
    $s.Save()
}

$startBat = Join-Path $AppRoot "START_CLINIC_LOCAL.bat"
$updatePs1 = Join-Path $AppRoot "scripts\update_client.ps1"

if (Test-Path $startBat) {
    New-ShortcutFile -ShortcutPath (Join-Path $desktop "Mo Phong Kham.lnk") -TargetPath $startBat -WorkingDirectory $AppRoot
}

if (Test-Path $updatePs1) {
    New-ShortcutFile `
        -ShortcutPath (Join-Path $desktop "Cap nhat Phong Kham.lnk") `
        -TargetPath "powershell.exe" `
        -Arguments "-ExecutionPolicy Bypass -File `"$updatePs1`"" `
        -WorkingDirectory $AppRoot
}

Write-Host "[DONE] Da tao shortcut desktop tren may nay."
