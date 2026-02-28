# Chạy MWL Server dưới dạng Windows Service

## Cách 1: Sử dụng NSSM (Recommended - Dễ nhất)

### Bước 1: Tải NSSM
- Tải NSSM từ: https://nssm.cc/download
- Giải nén vào thư mục `C:\nssm\` (hoặc thư mục bất kỳ)

### Bước 2: Mở PowerShell as Administrator
```powershell
# Cách 1: Click chuột phải vào PowerShell, chọn "Run as administrator"
# Cách 2: Nhấn Win + X, chọn "Windows PowerShell (Admin)"
```

### Bước 3: Cài đặt Service
```powershell
# Di chuyển đến thư mục NSSM
cd C:\nssm\win64

# Tạo service mới
.\nssm.exe install MWL_SERVER python.exe
```

### Bước 4: Cấu hình Service
Sẽ xuất hiện cửa sổ GUI:
1. **Path**: Chọn đường dẫn tới `python.exe`
   - Thường là: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311\python.exe`
   - Hoặc: `C:\Python311\python.exe`

2. **Startup directory**: Đặt thư mục dự án
   - `J:\DU_AN_AI\Phong_kham_dai_anh`

3. **Arguments**: Nhập
   - `mwl_server.py`

4. **Service name**: 
   - `MWL_SERVER`

5. Nhấn "Install service"

### Bước 5: Khởi động Service
```powershell
# Khởi động service
Start-Service MWL_SERVER

# Kiểm tra trạng thái
Get-Service MWL_SERVER

# Xem log
Get-EventLog -LogName Application -Source nssm | Select-Object -Last 10
```

### Bước 6: Đặt Service tự động khởi động khi khởi động Windows
```powershell
# Đặt chế độ khởi động tự động
Set-Service MWL_SERVER -StartupType Automatic
```

---

## Cách 2: Sử dụng Windows Task Scheduler

### Bước 1: Mở Task Scheduler
- Nhấn `Win + R`, gõ `taskschd.msc`, Enter

### Bước 2: Tạo Task mới
1. Nhấn chuột phải vào "Task Scheduler Library"
2. Chọn "Create Basic Task..."
3. Tên: `MWL Server`
4. Mô tả: `Modality Worklist Server for Voluson E10`

### Bước 3: Thiết lập Trigger
1. **When do you want the task to start?**: Chọn "At log on"
2. Nhấn Next

### Bước 4: Thiết lập Action
1. **Action**: Chọn "Start a program"
2. **Program/script**: `python.exe`
3. **Add arguments**: `mwl_server.py`
4. **Start in**: `J:\DU_AN_AI\Phong_kham_dai_anh`

### Bước 5: Hoàn thành
1. Nhấn Next
2. Đánh dấu "Open the Properties dialog for this task when I click Finish"
3. Nhấn Finish

### Bước 6: Cấu hình nâng cao
Trong Properties:
1. Tab "General":
   - Đánh dấu "Run whether user is logged in or not"
   - Chọn "Run with highest privileges"

2. Tab "Triggers":
   - Thêm "At startup" trigger ngoài "At logon"

3. Tab "Settings":
   - Đánh dấu "Run task as soon as possible after a scheduled start is missed"
   - Đánh dấu "If the task fails, restart every: 1 minute"
   - Đặt "If the task is still running, and it is time to create another instance, then stop the existing instance"

---

## Cách 3: Sử dụng Batch Script + Windows Scheduler (Đơn giản)

### Bước 1: Tạo file `.bat`
Tạo file `start_mwl_server.bat` trong thư mục dự án:

```batch
@echo off
REM Change to project directory
cd /d J:\DU_AN_AI\Phong_kham_dai_anh

REM Start MWL Server
python mwl_server.py

REM If it crashes, restart after 5 seconds
timeout /t 5
goto start

:start
python mwl_server.py
goto start
```

### Bước 2: Tạo Shortcut và đặt vào Startup
1. Tạo shortcut của file `.bat`
2. Nhấn chuột phải → Properties
3. Advanced... → Đánh dấu "Run as administrator"
4. Sao chép shortcut vào:
   - `C:\Users\<Username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

---

## Kiểm tra Service đang chạy

### Kiểm tra process
```powershell
Get-Process python | Where-Object { $_.ProcessName -like "*mwl*" }
```

### Kiểm tra port 104
```powershell
netstat -ano | findstr :104
```

### Xem log của service
```powershell
# Nếu dùng NSSM
Get-EventLog -LogName System -Source NSSM | Select-Object -Last 20
```

---

## Dừng/Khởi động Service

### Dừng service
```powershell
Stop-Service MWL_SERVER
```

### Khởi động service
```powershell
Start-Service MWL_SERVER
```

### Khởi động lại
```powershell
Restart-Service MWL_SERVER
```

---

## Gỡ cài đặt Service

```powershell
# Dừng service trước
Stop-Service MWL_SERVER

# Gỡ cài đặt
sc delete MWL_SERVER

# Hoặc nếu dùng NSSM
C:\nssm\win64\nssm.exe remove MWL_SERVER
```

---

## Khắc phục sự cố

### Service không khởi động
1. Kiểm tra đường dẫn Python:
```powershell
python --version
where python
```

2. Kiểm tra file `mwl_server.py` tồn tại

3. Xem log sự kiện Windows

### Lỗi Permission denied port 104
- Port 104 yêu cầu quyền admin
- Đảm bảo service chạy với quyền Administrator

### Service dừng sau vài giây
- Kiểm tra lỗi trong log
- Chạy thử: `python mwl_server.py` để xem lỗi chi tiết

---

## Tương lai: Auto-restart nếu crash

Tôi khuyên dùng NSSM vì nó có thể tự động restart service nếu bị crash.

Cấu hình trong NSSM GUI:
- AppExit Default: Restart
- AppRestartDelay: 5000 (milliseconds)
