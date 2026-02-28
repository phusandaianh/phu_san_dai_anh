# Setup MWL Server as Windows Service - Simple Version
# Run as Administrator

Write-Host "========================================" -ForegroundColor Green
Write-Host "MWL Server - Windows Service Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: Must run as Administrator!" -ForegroundColor Red
    exit 1
}

$projectDir = "J:\DU_AN_AI\Phong_kham_dai_anh"
$serviceName = "MWL_SERVER"

Write-Host "`nProject: $projectDir" -ForegroundColor Cyan

# Stop existing service
Write-Host "`nStopping existing service..." -ForegroundColor Yellow
Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Remove existing service
Write-Host "Removing existing service..." -ForegroundColor Yellow
Remove-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Create batch wrapper
Write-Host "Creating batch wrapper..." -ForegroundColor Yellow
$batchPath = Join-Path $projectDir "run_mwl_service.bat"
$batchContent = @"
@echo off
cd /d "$projectDir"
python mwl_server.py >> mwl_server.log 2>&1
"@
Set-Content -Path $batchPath -Value $batchContent -Encoding ASCII

# Create service
Write-Host "Creating Windows Service..." -ForegroundColor Yellow
New-Service `
    -Name $serviceName `
    -DisplayName "Modality Worklist Server (MWL)" `
    -BinaryPathName $batchPath `
    -StartupType Automatic `
    -Description "DICOM Modality Worklist Server for Voluson E10" | Out-Null

Write-Host "Starting service..." -ForegroundColor Yellow
Start-Service -Name $serviceName
Start-Sleep -Seconds 3

# Check status
$status = (Get-Service -Name $serviceName).Status
Write-Host "`nService Status: $status" -ForegroundColor Cyan

if ($status -eq "Running") {
    Write-Host "SUCCESS: Service is running!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Service may not have started properly" -ForegroundColor Yellow
}

# Display status
Write-Host "`n========================================" -ForegroundColor Green
Get-Service -Name $serviceName | Format-Table Name, DisplayName, Status, StartType
Write-Host "========================================" -ForegroundColor Green

Write-Host "`nUseful commands:" -ForegroundColor Cyan
Write-Host "  Get-Service MWL_SERVER" -ForegroundColor White
Write-Host "  Start-Service MWL_SERVER" -ForegroundColor White
Write-Host "  Stop-Service MWL_SERVER" -ForegroundColor White
Write-Host "  Restart-Service MWL_SERVER" -ForegroundColor White
Write-Host "  Get-Content '$projectDir\mwl_server.log' -Tail 50" -ForegroundColor White

Write-Host "`nSetup Complete!" -ForegroundColor Green
