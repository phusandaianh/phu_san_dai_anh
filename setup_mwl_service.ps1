# PowerShell Script: Setup MWL Server as Windows Service
# Run this as Administrator

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "Error: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Setting up MWL Server as Windows Service..." -ForegroundColor Green

# Configuration
$projectDir = "J:\DU_AN_AI\Phong_kham_dai_anh"
$serviceName = "MWL_SERVER"
$displayName = "Modality Worklist Server"
$pythonPath = (Get-Command python).Source
$scriptPath = Join-Path $projectDir "mwl_server.py"
$logPath = Join-Path $projectDir "mwl_server.log"

Write-Host "Project Directory: $projectDir" -ForegroundColor Cyan
Write-Host "Python Path: $pythonPath" -ForegroundColor Cyan
Write-Host "Script Path: $scriptPath" -ForegroundColor Cyan

# Verify paths exist
if (-not (Test-Path $projectDir)) {
    Write-Host "Error: Project directory not found: $projectDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $scriptPath)) {
    Write-Host "Error: Script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $pythonPath)) {
    Write-Host "Error: Python not found: $pythonPath" -ForegroundColor Red
    Write-Host "Please install Python or add it to PATH" -ForegroundColor Yellow
    exit 1
}

# Check if service already exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Service already exists. Removing..." -ForegroundColor Yellow
    Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Remove-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Create the service
Write-Host "Creating service: $serviceName..." -ForegroundColor Yellow

# Build command line
$arguments = "`"$pythonPath`" `"$scriptPath`""

# Create batch file wrapper
$batchPath = Join-Path $projectDir "run_mwl_service.bat"
$batchContent = @"
@echo off
cd /d "$projectDir"
"$pythonPath" "$scriptPath" >> "$logPath" 2>&1
"@

Set-Content -Path $batchPath -Value $batchContent -Encoding ASCII
Write-Host "Batch file created: $batchPath" -ForegroundColor Green

# Create Windows service
New-Service `
    -Name $serviceName `
    -DisplayName $displayName `
    -BinaryPathName $batchPath `
    -StartupType Automatic `
    -Description "DICOM Modality Worklist Server for Voluson E10 Ultrasound Machine" | Out-Null

Write-Host "Service created successfully!" -ForegroundColor Green

# Set service to run with high privileges
$service = Get-WmiObject Win32_Service -Filter "Name='$serviceName'"
$service.Change($null, $null, $null, $null, $null, $true) | Out-Null
Write-Host "Service configured to run with high privileges" -ForegroundColor Green

# Start the service
Write-Host "Starting service..." -ForegroundColor Yellow
Start-Service -Name $serviceName
Start-Sleep -Seconds 2

# Check if service is running
$running = (Get-Service -Name $serviceName).Status
if ($running -eq "Running") {
    Write-Host "✓ Service started successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Service failed to start" -ForegroundColor Red
}

# Display service status
Write-Host "`nService Status:" -ForegroundColor Green
Get-Service -Name $serviceName | Format-Table Name, DisplayName, Status, StartType

# Display useful commands
Write-Host "`n" + ("="*60) -ForegroundColor Green
Write-Host "Useful Commands:" -ForegroundColor Green
Write-Host "="*60
Write-Host "Start service:   Start-Service $serviceName" -ForegroundColor Cyan
Write-Host "Stop service:    Stop-Service $serviceName" -ForegroundColor Cyan
Write-Host "Restart service: Restart-Service $serviceName" -ForegroundColor Cyan
Write-Host "View status:     Get-Service $serviceName" -ForegroundColor Cyan
Write-Host "View logs:       Get-Content '$logPath' -Tail 50" -ForegroundColor Cyan
Write-Host "Remove service:  Remove-Service $serviceName -Force" -ForegroundColor Cyan

Write-Host "="*60 -ForegroundColor Green
Write-Host "✓ Setup complete!" -ForegroundColor Green
