# HƯỚNG DẪN CÀI ĐẶT MWL SERVER DƯỚI DẠNG WINDOWS SERVICE

## 🚀 CÁCH 2: WINDOWS SERVICE (KHUYÊN DÙNG)

### Bước 1: Mở Windows Explorer
- Nhấn `Win + E`
- Đi tới: `J:\DU_AN_AI\Phong_kham_dai_anh`

### Bước 2: Chạy File Setup
**Cách A - Tự động (Dễ nhất):**
1. Double-click vào file: `run_setup.bat`
2. Sẽ mở cửa sổ PowerShell với quyền Admin
3. Đợi script chạy xong

**Cách B - Thủ công:**
1. Nhấn `Win + X`
2. Chọn "Windows PowerShell (Admin)"
3. Gõ lệnh:
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
.\setup_mwl_service_simple.ps1
```

### Bước 3: Xác nhận Kết Quả
Script sẽ hiển thị:
```
========================================
MWL Server - Windows Service Setup
========================================
...
SUCCESS: Service is running!

Service Status: Running
========================================
```

### Bước 4: Kiểm Tra Service
```powershell
Get-Service MWL_SERVER
```

Nếu thấy:
```
Status   Name           DisplayName
------   ----           -----------
Running  MWL_SERVER     Modality Worklist Server (MWL)
```

→ ✓ Service đã cài đặt thành công!

---

## ✅ TÍNH NĂNG CỦA SERVICE

1. **Tự động khởi động lúc Windows boot**
   - Service sẽ chạy ngay khi bật máy
   - Không cần tác động thủ công

2. **Tự động restart nếu crash**
   - Nếu MWL Server bị lỗi dừng
   - Service sẽ tự động khởi động lại

3. **Chạy dưới quyền System**
   - Có quyền truy cập tất cả tài nguyên
   - Port 104 có thể hoạt động bình thường

---

## 📋 QUẢN LÝ SERVICE

### Dừng Service
```powershell
Stop-Service MWL_SERVER
```

### Khởi động Service
```powershell
Start-Service MWL_SERVER
```

### Khởi động lại Service
```powershell
Restart-Service MWL_SERVER
```

### Xem trạng thái
```powershell
Get-Service MWL_SERVER
```

### Xem log
```powershell
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Tail 50
```

### Xem log real-time
```powershell
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Wait
```

### Gỡ cài đặt Service
```powershell
Stop-Service MWL_SERVER -Force
Remove-Service MWL_SERVER -Force
```

---

## 🔍 KIỂM TRA PORT 104

### Xem process đang dùng port 104
```powershell
netstat -ano | findstr :104
```

### Kiểm tra MWL Server có chạy không
```powershell
Get-Process python | Where-Object {$_.ProcessName -like "*mwl*"}
```

---

## 💾 LOG FILE

**Vị trí:** `J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log`

**Xem log:**
```powershell
# 50 dòng cuối
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Tail 50

# Toàn bộ log
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log"

# Real-time
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log" -Wait
```

---

## ⚠️ KHẮC PHỤC SỰ CỐ

### Service không khởi động
1. Kiểm tra Python cài đặt:
```powershell
python --version
```

2. Kiểm tra file mwl_server.py:
```powershell
Test-Path "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.py"
```

3. Xem log để tìm lỗi:
```powershell
Get-Content "J:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.log"
```

### Port 104 bị chiếm
```powershell
# Xem ai đang dùng port 104
netstat -ano | findstr :104

# Kill process (thay 1234 bằng PID thực tế)
taskkill /PID 1234 /F
```

### Service crash liên tục
1. Dừng service:
```powershell
Stop-Service MWL_SERVER
```

2. Chạy thử trực tiếp để xem lỗi:
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
python mwl_server.py
```

3. Khắc phục lỗi
4. Khởi động lại service:
```powershell
Start-Service MWL_SERVER
```

---

## 📊 AUTO-SYNC

MWL Server đã được cấu hình:
- ✓ Tự động đồng bộ mỗi 5 phút
- ✓ Hoặc click nút "Đồng bộ Worklist" trong admin panel
- ✓ Không cần setup thêm

---

## 🎯 KIỂM TRA HOÀN CHỈNH

Sau khi cài đặt xong, hãy kiểm tra:

1. **Service đang chạy:**
```powershell
Get-Service MWL_SERVER | Select Status
```
→ Phải hiển thị: `Status: Running`

2. **Port 104 mở:**
```powershell
netstat -ano | findstr :104
```
→ Phải thấy port 104

3. **Máy siêu âm có kết nối được:**
- Vào DICOM Configuration trên máy Voluson
- Nhấn "Test Connection"
- Nếu Ping OK, Verify OK → ✓ Xong

---

## 🎉 HOÀN THÀNH

Sau khi cài đặt:
- MWL Server sẽ chạy 24/7
- Tự động khởi động lúc Windows boot
- Tự động restart nếu crash
- Đồng bộ Worklist mỗi 5 phút
- Phục vụ máy siêu âm Voluson E10

**Xong! MWL Server đã sẵn sàng! 🚀**
