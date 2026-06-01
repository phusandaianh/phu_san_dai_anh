<#
Cài Task Scheduler: khi đăng nhập Windows → chạy server :5000 + mở http://127.0.0.1:5000/

Chạy PowerShell **Run as Administrator** trong thư mục dự án:
  powershell -ExecutionPolicy Bypass -File .\install_clinic_autostart_task.ps1

Gỡ cài đặt:
  Unregister-ScheduledTask -TaskName CLINIC_APP_AUTOSTART -Confirm:$false
#>

param(
    [switch]$RunNow
)

$ErrorActionPreference = "Stop"

function Remove-ClinicStartupDuplicates {
    $startup = [Environment]::GetFolderPath("Startup")
    @(
        "PhongKhamDaiAnh_Autostart.cmd",
        "Phong Kham Dai Anh.lnk",
        "run_server.bat"
    ) | ForEach-Object {
        $path = Join-Path $startup $_
        if (Test-Path $path) {
            Remove-Item $path -Force
            Write-Host "  Da xoa Startup: $_" -ForegroundColor Yellow
        }
    }
}

function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "LOI: Can chay PowerShell voi quyen Administrator." -ForegroundColor Red
    Write-Host "     Chuot phai PowerShell -> Run as administrator" -ForegroundColor Yellow
    exit 1
}

$ProjectDir = $PSScriptRoot
$Launcher = Join-Path $ProjectDir "scripts\clinic_autostart_launcher.ps1"
$TaskName = "CLINIC_APP_AUTOSTART"

if (-not (Test-Path $Launcher)) {
    throw "Khong tim thay: $Launcher"
}

$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    throw "Khong tim thay python.exe trong PATH. Hay cai Python va them vao PATH."
}

$PsArgs = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Launcher`""

Write-Host "Don dep Startup trung (chi dung Task Scheduler)..." -ForegroundColor Cyan
Remove-ClinicStartupDuplicates
$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $PsArgs `
    -WorkingDirectory $ProjectDir

$CurrentUser = "$env:USERDOMAIN\$env:USERNAME"
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser
$TriggerLogon.Delay = "PT45S"

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Limited

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch { }

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $TriggerLogon `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Tu dong khoi dong Phong kham Dai Anh (127.0.0.1:5000) va mo trinh duyet khi dang nhap" `
    -Force | Out-Null

Write-Host ""
Write-Host "Da tao task: $TaskName" -ForegroundColor Green
Write-Host "  Thu muc:  $ProjectDir" -ForegroundColor Cyan
Write-Host "  Python:   $PythonPath" -ForegroundColor Cyan
Write-Host "  Trigger:  Dang nhap ($CurrentUser), tre 45 giay" -ForegroundColor Cyan
Write-Host "  URL:      http://127.0.0.1:5000/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Kiem tra ngay (mo trinh duyet neu server chua chay):" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host ""
Write-Host "Go bo:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
Write-Host ""

if ($RunNow) {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Da kich hoat task. Doi ~1 phut roi kiem tra trinh duyet va file clinic_autostart.log" -ForegroundColor Green
}
