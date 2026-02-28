# HƯỚNG DẪN CHẠY MWL SERVER BACKGROUND - NHANH NHẤT

## Cách 1: Sử dụng PowerShell Script (KHUYÊN DÙNG - 1 lệnh)

### Bước 1: Mở PowerShell as Administrator
1. Nhấn `Win + X`
2. Chọn "Windows PowerShell (Admin)" hoặc "Terminal (Admin)"

### Bước 2: Chạy script setup
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
.\setup_mwl_service.ps1
```

### Bước 3: Xác nhận
- Script sẽ hiển thị các bước setup
- Nếu thấy "✓ Service started successfully!" → Xong!

---

## Cách 2: Sử dụng Batch File (Thủ công nhất)

### Bước 1: Chạy file batch
Double-click vào file `start_mwl_server.bat`

### Bước 2: Cho phép chạy
- Nếu hỏi "Do you want to allow...", chọn "Yes"

### Bước 3: Cửa sổ sẽ mở lên
- Để cửa sổ mở, server sẽ chạy nền

**Lưu ý**: Nếu đóng cửa sổ, server sẽ dừng

---

## Cách 3: Sử dụng Windows Task Scheduler (Chậm nhất)

### Bước 1: Tạo task tự động khởi động

Chạy lệnh này trong PowerShell (Admin):

```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c start /min J:\DU_AN_AI\Phong_kham_dai_anh\start_mwl_server.bat"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -RunLevel Highest
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Description "MWL Server"
Register-ScheduledTask -TaskName "MWL Server" -InputObject $task -Force
```

### Bước 2: Khởi động lần đầu
```powershell
Start-ScheduledTask -TaskName "MWL Server"
```

---

## KIỂM TRA TRẠNG THÁI

### Kiểm tra xem server có chạy không
```powershell
# Phương pháp 1: Kiểm tra process
Get-Process python | Where-Object {$_.ProcessName -like "*mwl*"}

# Phương pháp 2: Kiểm tra port 104
netstat -ano | findstr :104

# Phương pháp 3: Kiểm tra service (nếu dùng setup script)
Get-Service MWL_SERVER
```

---

## DỪNG/KHỞI ĐỘNG LẠI

### Dừng service
```powershell
Stop-Service MWL_SERVER
```

### Khởi động lại
```powershell
Start-Service MWL_SERVER
```

### Khởi động lại server
```powershell
Restart-Service MWL_SERVER
```

---

## XEM LOG

### Xem log file
```powershell
# Xem 50 dòng cuối cùng
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Tail 50

# Xem toàn bộ log
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log"

# Xem log real-time
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Wait
```

---

## KHẮC PHỤC SỰ CỐ

### Server không khởi động
1. Kiểm tra Python được cài đặt:
```powershell
python --version
```

2. Kiểm tra tệp mwl_server.py tồn tại:
```powershell
Test-Path "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.py"
```

3. Chạy thử trực tiếp:
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
python mwl_server.py
```

### Port 104 bị chiếm
```powershell
# Xem process đang dùng port 104
netstat -ano | findstr :104

# Kill process (thay PID bằng số thực tế)
taskkill /PID <PID> /F
```

### Service tự động dừng
1. Xem log để tìm lỗi
2. Kiểm tra dependencies (mwl_sync.py, mwl_store.py có không)
3. Chạy trong terminal để xem lỗi chi tiết

---

## GỠ CÀI ĐẶT SERVICE

```powershell
# Dừng service
Stop-Service MWL_SERVER -Force

# Gỡ cài đặt
Remove-Service -Name MWL_SERVER -Force
```

---

## TÓM TẮT

| Cách | Ưu điểm | Nhược điểm |
|------|---------|-----------|
| PowerShell Script | Tự động, tiện, dễ | Cần run as Admin |
| Batch File | Đơn giản | Cần giữ cửa sổ mở |
| Task Scheduler | Tự động khởi động | Phức tạp hơn |

**KHUYÊN DÙNG: PowerShell Script - Chỉ cần 1 lệnh duy nhất!**
