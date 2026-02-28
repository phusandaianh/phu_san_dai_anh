<#
Create a Windows Scheduled Task to run mwl_sync.py every 5 minutes.

Run this script in an elevated PowerShell (Run as Administrator).

It will create a task named "MWL Sync" that runs Python and executes mwl_sync.py.
#>

$TaskName = 'MWL Sync'
$ScriptPath = Join-Path -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) -ChildPath 'mwl_sync.py'
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    Write-Error "python not found in PATH. Please ensure Python is installed and available in PATH."
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "Run MWL sync every 5 minutes" -Force
    Write-Output "Scheduled Task '$TaskName' created. It will run every 5 minutes."
} catch {
    Write-Error "Failed to create scheduled task: $_"
}
