# 🚀 HƯỚNG DẪN CHẠY SERVERS

## 📋 CÁCH 1: Dùng Batch File (Đơn Giản Nhất)

### Bước 1: Mở File Explorer
1. Vào thư mục: `J:\DU_AN_AI\Phong_kham_dai_anh`
2. Tìm file: `start_all_servers.bat`
3. **Double-click** vào file đó

### Bước 2: Xác Nhận
- Sẽ mở **3 cửa sổ command prompt**:
  1. **Cửa sổ chính**: Hiển thị hướng dẫn
  2. **Cửa sổ "Web Server"**: Chạy `app.py` (port 5000)
  3. **Cửa sổ "DICOM MWL Server"**: Chạy `dicom_mwl_server.py` (port 104)

### Bước 3: Kiểm Tra
- **Web Server** sẽ hiển thị: 
  ```
  * Running on http://127.0.0.1:5000
  ```

- **DICOM MWL Server** sẽ hiển thị:
  ```
  ============================================================
  DICOM MODALITY WORKLIST (MWL) SERVER
  ============================================================
  AE Title: CLINIC_SYSTEM
  Port: 104
  Cho Voluson E10 query worklist...
  ============================================================
  ```

---

## 📋 CÁCH 2: Chạy Thủ Công (Terminal)

### Bước 1: Mở 2 Terminal

**Terminal 1 - PowerShell:**
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
python app.py
```

**Terminal 2 - PowerShell (mở cửa sổ mới):**
```powershell
cd J:\DU_AN_AI\Phong_kham_dai_anh
python dicom_mwl_server.py
```

### Bước 2: Kiểm Tra

**Terminal 1** (Web Server):
```
* Running on http://127.0.0.1:5000
* Press CTRL+C to quit
```

**Terminal 2** (DICOM Server):
```
============================================================
DICOM MODALITY WORKLIST (MWL) SERVER
============================================================
AE Title: CLINIC_SYSTEM
Port: 104
Database: clinic.db
============================================================
Cho Voluson E10 query worklist...
```

---

## ✅ KIỂM TRA SERVERS ĐANG CHẠY

### Mở PowerShell và chạy:
```powershell
# Kiểm tra port 5000 (Web Server)
netstat -ano | findstr 5000

# Kiểm tra port 104 (DICOM Server)
netstat -ano | findstr 104
```

**Kết quả mong đợi:**
```
TCP    0.0.0.0:5000           0.0.0.0:0              LISTENING
TCP    0.0.0.0:104            0.0.0.0:0              LISTENING
```

---

## 🌐 TRUY CẬP WEB

Sau khi servers khởi động, mở trình duyệt:

```
http://127.0.0.1:5000
```

Hoặc:

```
http://localhost:5000
```

---

## 🧪 TEST CONNECTION

### Test DICOM Server:

```powershell
# Test kết nối từ máy clinic tới Voluson
Test-NetConnection -ComputerName 10.17.2.1 -Port 104
```

**Kết quả mong đợi:**
```
ComputerName     : 10.17.2.1
RemoteAddress    : 10.17.2.1
RemotePort       : 104
TcpTestSucceeded : True  ✅
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### 1. **Phải giữ cả 2 terminal mở**
- Đóng 1 trong 2 terminal = Server đó sẽ tắt
- Máy Voluson E10 không query được nếu DICOM server tắt

### 2. **Không nhấn CTRL+C**
- Nhấn CTRL+C sẽ tắt server
- Chỉ tắt khi muốn dừng toàn bộ hệ thống

### 3. **Kiểm tra Firewall**
Nếu không kết nối được, có thể firewall chặn port 104:

```powershell
# Mở port 104 trong Windows Firewall
New-NetFirewallRule -DisplayName "DICOM MWL Server" -Direction Inbound -LocalPort 104 -Protocol TCP -Action Allow
```

---

## 🛑 DỪNG SERVERS

### Cách 1: Tắt Terminal
- Nhấn **CTRL+C** trong từng terminal
- Hoặc đóng cửa sổ terminal

### Cách 2: Tắt Tất Cả
```powershell
# Tắt tất cả Python processes
Get-Process python | Stop-Process
```

**⚠️ Cảnh báo**: Lệnh này sẽ tắt TẤT CẢ chương trình Python!

---

## 📝 LOG VÀ DEBUG

### Xem Logs:

**Web Server** (Terminal 1):
- Hiển thị mọi HTTP request
- Hiển thị lỗi nếu có

**DICOM Server** (Terminal 2):
- Hiển thị khi có C-ECHO request
- Hiển thị khi có C-FIND request
- Hiển thị query parameters

### Ví dụ Log DICOM Server:
```
INFO:dicom_mwl_server:Nhận được C-ECHO từ VOLUSON_E10
INFO:dicom_mwl_server:Nhận được C-FIND từ VOLUSON_E10
INFO:dicom_mwl_server:Truy vấn: Modality=US, Ngày=20251030
```

---

## 🔄 KHỞI ĐỘNG LẠI

Nếu gặp lỗi, làm theo thứ tự:

1. **Dừng tất cả servers** (CTRL+C)
2. **Đợi 5 giây**
3. **Khởi động lại** (`start_all_servers.bat`)

---

## ✅ CHECKLIST

Sau khi khởi động, kiểm tra:

- [ ] Có 2 terminal đang chạy
- [ ] Terminal 1: Web Server trên port 5000
- [ ] Terminal 2: DICOM Server trên port 104
- [ ] Truy cập http://127.0.0.1:5000 thành công
- [ ] Test-NetConnection port 104 thành công
- [ ] Không có lỗi trong cả 2 terminal

---

## 🆘 GẶP VẤN ĐỀ?

### Lỗi "Port already in use"
**Nguyên nhân**: Port 5000 hoặc 104 đang được dùng

**Giải pháp**:
```powershell
# Tìm process đang dùng port
netstat -ano | findstr 5000
netstat -ano | findstr 104

# Tắt process (thay PID bằng số thật)
taskkill /PID <PID> /F
```

### Lỗi "No module named pynetdicom"
**Nguyên nhân**: Chưa cài đặt thư viện

**Giải pháp**:
```powershell
pip install pynetdicom pydicom
```

### Lỗi "database is locked"
**Nguyên nhân**: Database đang được dùng bởi process khác

**Giải pháp**: Tắt tất cả Python và khởi động lại

---

**🎉 Sau khi servers chạy thành công, test trên Voluson E10!**

