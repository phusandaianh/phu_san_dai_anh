<#
Install auto-start for MWL server using Windows Task Scheduler.

How to run:
1) Open PowerShell as Administrator
2) cd J:\DU_AN_AI\Phong_kham_dai_anh
3) powershell -ExecutionPolicy Bypass -File .\install_mwl_autostart_task.ps1
#>

$ErrorActionPreference = "Stop"

function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "ERROR: Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

$ProjectDir = "J:\DU_AN_AI\Phong_kham_dai_anh"
$ScriptPath = Join-Path $ProjectDir "mwl_server.py"
$TaskName = "MWL_SERVER_AUTOSTART"
$LogPath = Join-Path $ProjectDir "mwl_server_task.log"

if (-not (Test-Path $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}
if (-not (Test-Path $ScriptPath)) {
    throw "Script not found: $ScriptPath"
}

# Resolve python.exe absolute path (avoid PATH issues in Task Scheduler)
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    throw "python.exe not found in PATH. Please install Python or add to PATH."
}

# Run via cmd to force working directory + append stdout/stderr to log file
$CmdArgs = "/c cd /d `"$ProjectDir`" && `"$PythonPath`" -X utf8 -u `"$ScriptPath`" >> `"$LogPath`" 2>&1"
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $CmdArgs -WorkingDirectory $ProjectDir

# Trigger only at logon (mapped drive like J: is more likely ready)
$CurrentUser = "$env:USERDOMAIN\$env:USERNAME"
$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $CurrentUser
$TriggerLogon.Delay = "PT30S"

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Days 3650) `
    -MultipleInstances IgnoreNew `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

# Run under local account with highest privileges
$Principal = New-ScheduledTaskPrincipal `
    -UserId $CurrentUser `
    -LogonType Interactive `
    -RunLevel Highest

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
} catch {
    # ignore
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger @($TriggerLogon) `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Auto-start MWL Server (mwl_server.py) at user logon" `
    -Force | Out-Null

Write-Host "Created task: $TaskName" -ForegroundColor Green
Write-Host "Action: cmd.exe $CmdArgs" -ForegroundColor Cyan
Write-Host "Python: $PythonPath" -ForegroundColor Cyan
Write-Host "Triggers: At logon ($CurrentUser) +30s" -ForegroundColor Cyan

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 2

$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host ""
Write-Host "Task status:" -ForegroundColor Green
Write-Host ("  State: " + $task.State)
Write-Host ("  LastRunTime: " + $info.LastRunTime)
Write-Host ("  LastTaskResult: " + $info.LastTaskResult)
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName $TaskName"
Write-Host "  Get-ScheduledTaskInfo -TaskName $TaskName"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
