# CÁCH CHẠY MWL SERVER BACKGROUND - BẢN IN ẤN

## CÁCH 1: Chạy Batch File (Nhanh nhất - Khuyến cáo)

### Bước 1: Tìm file trong Windows Explorer
```
Đường dẫn: J:\DU_AN_AI\Phong_kham_dai_anh\start_mwl_server.bat
```

### Bước 2: Double-click vào file
- File sẽ mở cửa sổ Command Prompt
- Sẽ thấy dòng chữ: "Starting MWL Server..."

### Bước 3: Để cửa sổ mở
- **ĐỪ KHÔNG ĐÓNG CỬA SỔ này** - Server sẽ chạy nền
- Bạn có thể phóng to/thu nhỏ hoặc di chuyển sang bên
- Nếu đóng cửa sổ → Server dừng

### Bước 4: Xác nhận server chạy
Mở PowerShell mới (không cần đóng batch):
```powershell
netstat -ano | findstr :104
```

Nếu thấy dòng có port 104 → Server đang chạy ✓

---

## CÁCH 2: Chạy Permanent Service (Khởi động tự động)

### Bước 1: Mở PowerShell as Administrator
1. Nhấn `Win + X`
2. Chọn "Windows PowerShell (Admin)"

### Bước 2: Copy-Paste lệnh này
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
.\setup_mwl_service.ps1
```

### Bước 3: Đợi kết quả
- Script sẽ tạo Windows Service tự động
- Nếu thấy "✓ Service started successfully!" → Xong!

### Bước 4: Kiểm tra
```powershell
Get-Service MWL_SERVER
```

Nếu Status = "Running" → Server đang chạy ✓

---

## CÁCH 3: Tạo Startup Shortcut (Dễ nhất cho người mới)

### Bước 1: Mở Windows Explorer
```
Nhấn Win + E
Đi tới: J:\DU_AN_AI\Phong_kham_dai_anh
```

### Bước 2: Click chuột phải trên file `start_mwl_server.bat`
- Chọn "Create shortcut"
- Shortcut sẽ được tạo cùng thư mục

### Bước 3: Di chuyển Shortcut vào Startup
1. Nhấn `Win + R`
2. Gõ: `shell:startup`
3. Nhấn Enter
4. Sao chép file shortcut vào thư mục này

### Bước 4: Từ giờ, mỗi khi khởi động Windows
- Shortcut sẽ tự động chạy
- MWL Server sẽ khởi động background
- Sẽ có cửa sổ Command Prompt ở Taskbar

---

## KIỂM TRA SERVER CÓ CHẠY KHÔNG

### Cách 1: Kiểm tra Port
```powershell
netstat -ano | findstr :104
```

Nếu thấy dòng có port 104 → ✓ Server chạy

### Cách 2: Kiểm tra Process Python
```powershell
Get-Process python | Where-Object {$_.ProcessName -like "*mwl*"}
```

Nếu thấy process python → ✓ Server chạy

### Cách 3: Kiểm tra Service Status
```powershell
Get-Service MWL_SERVER
```

Nếu Status = Running → ✓ Server chạy

---

## DỪNG SERVER

### Nếu dùng Batch File
- Đóng cửa sổ Command Prompt

### Nếu dùng Windows Service
```powershell
Stop-Service MWL_SERVER
```

---

## KHỞI ĐỘNG LẠI SERVER

### Nếu dùng Batch File
- Chạy lại `start_mwl_server.bat`

### Nếu dùng Windows Service
```powershell
Restart-Service MWL_SERVER
```

---

## XEM LOG/LỖI

```powershell
# Xem log file (nếu chạy batch)
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Tail 20

# Xem real-time
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Wait
```

---

## KHUYÊN CÁC

**Lần đầu tiên:**
- Sử dụng **CÁCH 1 (Batch File)** để test nhanh
- Để cửa sổ mở để xem log
- Sau đó dùng **CÁCH 2 (Service)** để chạy permanent

**Sản xuất:**
- Dùng **CÁCH 2 (Service)** hoặc **CÁCH 3 (Startup Shortcut)**
- Server sẽ chạy tự động khi khởi động Windows
- Không cần tác động thủ công

---

## AUTO-SYNC MỖI 5 PHÚT

MWL Server đã được cấu hình:
- Tự động đồng bộ Worklist từ clinic.db mỗi 5 phút
- Hoặc click nút "Đồng bộ Worklist" trong admin panel

Không cần cấu hình gì thêm!

---

## SOẠN HỘI LIÊN HỆ

- **Email**: support@phong-kham-dai-anh.com
- **Phone**: 0x-xxxx-xxxx
- **Support Team**: MWL Server Support

Chúc bạn thành công! 🎉
