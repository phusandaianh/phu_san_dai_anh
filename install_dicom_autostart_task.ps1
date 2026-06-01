<#
Cai Task Scheduler: tu dong chay ngam DICOM + Worklist cho may sieu am.

Chay PowerShell **Run as Administrator** trong thu muc du an:
  powershell -ExecutionPolicy Bypass -File .\install_dicom_autostart_task.ps1 -RunNow

Gỡ:
  Unregister-ScheduledTask -TaskName DICOM_SERVICES_AUTOSTART -Confirm:$false
#>

param([switch]$RunNow)

$ErrorActionPreference = "Stop"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "LOI: Can quyen Administrator." -ForegroundColor Red
    exit 1
}

$ProjectDir = $PSScriptRoot
$Launcher = Join-Path $ProjectDir "scripts\dicom_autostart_launcher.ps1"
$TaskName = "DICOM_SERVICES_AUTOSTART"
$LegacyTask = "MWL_SERVER_AUTOSTART"

if (-not (Test-Path $Launcher)) {
    throw "Khong tim thay: $Launcher"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Khong tim thay python.exe trong PATH"
}

function Add-DicomFirewallRules {
    $rules = @(
        @{ Name = "PKDA DICOM MWL In"; Port = 104 },
        @{ Name = "PKDA DICOM C-STORE In"; Port = 11112 },
        @{ Name = "PKDA Orthanc DICOM In"; Port = 4242 }
    )
    foreach ($r in $rules) {
        $existing = netsh advfirewall firewall show rule name=$($r.Name) 2>$null
        if ($LASTEXITCODE -ne 0) {
            netsh advfirewall firewall add rule name=$($r.Name) dir=in action=allow protocol=TCP localport=$($r.Port) | Out-Null
            Write-Host "  Firewall: $($r.Name) port $($r.Port)" -ForegroundColor Cyan
        }
    }
}

Write-Host "Cau hinh firewall (DICOM)..." -ForegroundColor Cyan
Add-DicomFirewallRules

# Go task cu (hien cua so CMD)
try {
    Unregister-ScheduledTask -TaskName $LegacyTask -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "  Da go task cu: $LegacyTask" -ForegroundColor Yellow
} catch { }

$PsArgs = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Launcher`""
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $PsArgs -WorkingDirectory $ProjectDir

$CurrentUser = "$env:USERDOMAIN\$env:USERNAME"
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser
$Trigger.Delay = "PT90S"

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Highest

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch { }

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Tu dong: MWL worklist :104 + DICOM C-STORE :11112 + Orthanc (neu co) cho may sieu am" `
    -Force | Out-Null

Write-Host ""
Write-Host "Da tao task: $TaskName" -ForegroundColor Green
Write-Host "  Thu muc:     $ProjectDir" -ForegroundColor Cyan
Write-Host "  Trigger:     Dang nhap +90 giay (sau web app)" -ForegroundColor Cyan
Write-Host "  MWL:         mwl_server.py  -> port 104  (CLINIC_SYSTEM)" -ForegroundColor Cyan
Write-Host "  C-STORE:     dicom_receiver.py -> port 11112 (AE: PC)" -ForegroundColor Cyan
Write-Host "  Orthanc:     neu co orthanc\bin\Orthanc.exe -> port 4242" -ForegroundColor Cyan
Write-Host "  Log:         dicom_autostart.log" -ForegroundColor Cyan
Write-Host ""
Write-Host "Kiem tra: Get-ScheduledTask -TaskName $TaskName" -ForegroundColor Yellow
Write-Host "Chay thu: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor Yellow
Write-Host ""

if ($RunNow) {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Da kich hoat task. Doi ~2 phut, kiem tra dicom_autostart.log" -ForegroundColor Green
}
