# Xoa cac file Startup cu (mo cua so CMD). Chi giu Task Scheduler CLINIC_APP_AUTOSTART.
$startup = [Environment]::GetFolderPath("Startup")
$removed = @()
@(
    "PhongKhamDaiAnh_Autostart.cmd",
    "Phong Kham Dai Anh.lnk",
    "run_server.bat"
) | ForEach-Object {
    $path = Join-Path $startup $_
    if (Test-Path $path) {
        Remove-Item $path -Force
        $removed += $_
    }
}
if ($removed.Count -eq 0) {
    Write-Host "Khong con file Startup trung." -ForegroundColor Green
} else {
    Write-Host "Da xoa:" -ForegroundColor Green
    $removed | ForEach-Object { Write-Host "  - $_" }
}
