# 📱 HƯỚNG DẪN CÀI ĐẶT WORKLIST TRÊN VOLUSON E10

**Ngày cập nhật:** 11 November 2025  
**Hệ thống:** Phòng Khám Đại Anh - Voluson E10 Integration  
**Mục đích:** Kết nối máy siêu âm Voluson E10 với Worklist server (DICOM)

---

## 🎯 MỤC TIÊU

Sau hướng dẫn này, Voluson E10 sẽ:
✅ Kết nối được với Worklist server  
✅ Hiển thị danh sách bệnh nhân  
✅ Tải thông tin appointment tự động  
✅ Lưu kết quả siêu âm lên hệ thống  

---

## 📋 YÊU CẦU TIÊN QUYẾT

### Trên Server (Phòng Khám):
- ✅ MWL Server đang chạy (port 104)
- ✅ Database có thông tin bệnh nhân
- ✅ Appointments đã được nhập
- ✅ Network kết nối được Voluson E10

### Trên Voluson E10:
- ✅ Kết nối mạng LAN (IP 10.17.2.1)
- ✅ Có quyền truy cập DICOM settings
- ✅ Phiên bản firmware hỗ trợ DICOM Worklist

### Network:
- ✅ Server IP: 10.17.2.2 (hoặc IP clinic server)
- ✅ Voluson IP: 10.17.2.1
- ✅ Port 104 mở giữa hai máy
- ✅ Ping được từ Voluson đến Server

---

## 🚀 BƯỚC 1: KHỞI ĐỘNG WORKLIST SERVER

### 1.1 Chạy trên Server (Phòng Khám)

**Option A: Mode phát triển (Development)**
```bash
cd j:\DU_AN_AI\Phong_kham_dai_anh

# Terminal 1: Flask App
python app.py

# Terminal 2: MWL Server
python mwl_server.py
```

**Output mong đợi:**
```
INFO:werkzeug: * Running on http://127.0.0.1:5000/
INFO:pynetdicom: Starting MWL SCP on port 104
INFO:pynetdicom: AE Title: CLINIC_SYSTEM
```

**Option B: Mode sản xuất (Production)**
```bash
# Chạy as Administrator
.\run_setup.bat
```

**Output mong đợi:**
```
Service 'PK_DaiAnh_MWL' installed successfully
Service started successfully
```

### 1.2 Kiểm tra Server chạy OK

```bash
# Trên server, chạy lệnh này để xác minh
netstat -ano | findstr ":104"
```

**Output mong đợi:**
```
TCP    0.0.0.0:104    0.0.0.0:0    LISTENING    12345
```

Nếu thấy dòng này = Server đang lắng nghe port 104 ✅

---

## 🔧 BƯỚC 2: CẤU HÌNH VOLUSON E10

### 2.1 Vào DICOM Settings

**Trên máy Voluson E10:**

1. Nhấn menu **Home** (màn hình chính)
2. Tìm **Setup** hoặc **System Settings**
3. Chọn **DICOM** hoặc **Networking**
4. Chọn **Modality Worklist** hoặc **DICOM Services**

*(Các bước có thể khác tùy phiên bản Voluson, hãy xem hướng dẫn máy)*

### 2.2 Thêm Server Worklist

**Tìm section:** "DICOM Servers" hoặc "Worklist Configuration"

**Thêm server mới:**

| Trường | Giá trị | Ghi chú |
|-------|--------|---------|
| **Server Name** | `Phong_Kham_Dai_Anh` | Tên để nhận dạng |
| **Server IP Address** | `10.17.2.2` | IP của clinic server |
| **Port** | `104` | DICOM standard port |
| **AE Title (Local)** | `VOLUSON_E10` | AE Title của máy siêu âm |
| **AE Title (Remote)** | `CLINIC_SYSTEM` | AE Title của server |
| **Type** | `Modality Worklist` | Loại dịch vụ |

**Ví dụ cầu hình:**
```
┌─────────────────────────────────────────┐
│  DICOM Worklist Server Configuration    │
├─────────────────────────────────────────┤
│  Server Name:        Phong_Kham_Dai_Anh │
│  IP Address:         10.17.2.2          │
│  Port:               104                │
│  Local AE Title:     VOLUSON_E10        │
│  Remote AE Title:    CLINIC_SYSTEM      │
│  Service Type:       Modality Worklist  │
│                                         │
│  [Save] [Test] [Cancel]                │
└─────────────────────────────────────────┘
```

### 2.3 Lưu cấu hình

- Nhấn **Save** hoặc **OK**
- Chờ máy khởi động lại (nếu cần)

---

## ✅ BƯỚC 3: KIỂM TRA KẾT NỐI

### 3.1 Test Connection từ Voluson

**Trên Voluson E10:**

1. Vào **DICOM Settings**
2. Chọn server vừa tạo: `Phong_Kham_Dai_Anh`
3. Nhấn **Test Connection** hoặc **Verify**

**Kết quả thành công:**
```
✅ Connection successful
✅ Server responding
✅ Worklist available
```

**Nếu lỗi, xem phần Troubleshooting bên dưới**

### 3.2 Test Connection từ Server (Optional)

**Trên Server (máy clinic), dùng DICOM client:**

```bash
# Kiểm tra xem port 104 có lắng nghe
netstat -ano | findstr :104

# Hoặc dùng Python DICOM test
python -c "
from pynetdicom import AE
ae = AE(ae_title='TEST')
assoc = ae.associate('10.17.2.1', 104, ae_title='VOLUSON_E10')
print('Connection OK' if assoc else 'Connection Failed')
"
```

---

## 🔄 BƯỚC 4: TRUY CẬP DANH SÁCH BỆNH NHÂN

### 4.1 Trên Voluson E10

**Để xem danh sách bệnh nhân từ Worklist:**

1. Vào **Patient** hoặc **New Patient**
2. Chọn **Query Worklist** hoặc **Search Worklist**
3. Chọn server: `Phong_Kham_Dai_Anh`
4. Nhấn **Search** hoặc **Query**

**Kết quả mong đợi:**
```
Patient List from Worklist:
┌─────────────────────────────────────────┐
│ Patient ID | Patient Name | Modality   │
├─────────────────────────────────────────┤
│ 1          | Nguyễn Thị Test | US     │
│ 1          | Hà Ngọc Đại  | US       │
└─────────────────────────────────────────┘

[Select] [Refresh] [Cancel]
```

### 4.2 Lấy thông tin bệnh nhân

1. Chọn bệnh nhân từ danh sách
2. Nhấn **Select** hoặc **Load**
3. Thông tin appointment sẽ được tải:
   - Tên bệnh nhân
   - ID bệnh nhân
   - Mô tả kiểm tra (Siêu âm thai)
   - Ngày giờ appointment

---

## 📊 BƯỚC 5: THỰC HIỆN SIÊU ÂM

### 5.1 Quá trình siêu âm

1. Đã load thông tin bệnh nhân từ Worklist ✅
2. Thực hiện quét siêu âm
3. Thêm số đo, nhận xét
4. Tạo report

### 5.2 Lưu kết quả

**Trên Voluson E10:**

1. Sau khi siêu âm xong
2. Chọn **Save** hoặc **Export**
3. Chọn **DICOM Export** (nếu có)
4. Chọn **Send to Server** (tùy chọn)

**Hoặc:**
1. **Save as PDF** (report)
2. **Export Images** (hình ảnh siêu âm)

---

## 🔍 BƯỚC 6: KIỂM TRA DỮ LIỆU ĐỒNG BỘ

### 6.1 Trên Web Admin (Port 5000)

**Truy cập:** http://10.17.2.2:5000/admin.html

**Hoặc trên server:** http://localhost:5000/admin.html

**Kiểm tra:**
1. Vào **Appointments** hoặc **Patient List**
2. Xác nhận bệnh nhân vừa siêu âm đã được lưu
3. Xem **Exam Results** hoặc **Ultrasound Results**

### 6.2 Kiểm tra MWL Database

**Trên server:**

```bash
# Xem số lượng entries
python -c "
import mwl_store
mwl_store.init_db()
entries = mwl_store.get_all_entries()
print(f'Total MWL entries: {len(entries)}')
"

# Xem chi tiết entries
python -c "
import sqlite3, json
conn = sqlite3.connect('mwl.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM worklist_entries LIMIT 5')
for row in cursor.fetchall():
    print(json.loads(row[0]))
"
```

---

## 🔐 CẤU HÌNH SECURITY (Tùy chọn)

### 6.1 Cấu hình AE Title Restrictions

**Nếu muốn chỉ cho phép VOLUSON_E10 kết nối:**

Chỉnh sửa `mwl_server.py`:

```python
# Hãy tìm dòng này:
ALLOWED_AE_TITLES = ['VOLUSON_E10', '*']  # Allow any

# Và thay đổi thành:
ALLOWED_AE_TITLES = ['VOLUSON_E10']  # Only Voluson
```

Sau đó restart MWL server.

### 6.2 Cấu hình Port Firewall

**Nếu dùng Windows Firewall:**

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "DICOM Port 104" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 104

# Verify rule
Get-NetFirewallRule -DisplayName "DICOM Port 104"
```

---

## ⚡ BƯỚC 7: TỐI ƯU HÓA CẤU HÌNH

### 7.1 Cấu hình Auto-sync

**MWL Server tự động đồng bộ mỗi 5 phút:**

Kiểm tra logs:
```bash
tail -f mwl_server.log
```

**Nếu muốn thay đổi thời gian đồng bộ, sửa `mwl_server.py`:**

```python
# Tìm dòng:
scheduler.add_job(sync_worklist, 'interval', minutes=5)

# Thay đổi thành (ví dụ: 2 phút):
scheduler.add_job(sync_worklist, 'interval', minutes=2)
```

### 7.2 Cấu hình Logging

**Để ghi log chi tiết, thêm vào `mwl_server.py`:**

```python
import logging

logging.basicConfig(
    filename='mwl_server.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

## 🐛 TROUBLESHOOTING

### Vấn đề 1: Voluson không kết nối được Server

**Triệu chứng:**
```
❌ Connection failed
❌ Server not responding
❌ Timeout
```

**Nguyên nhân & Cách khắc phục:**

| Nguyên nhân | Cách kiểm tra | Cách khắc phục |
|-----------|---------------|---------------|
| MWL Server không chạy | `netstat -ano \| findstr :104` | `python mwl_server.py` |
| IP Server sai | Ping 10.17.2.2 từ Voluson | Dùng IP đúng |
| Port 104 blocked | `netstat -ano \| findstr :104` | Mở firewall port 104 |
| AE Title sai | Check Voluson settings | Thay AE Title thành CLINIC_SYSTEM |
| Network disconnect | Ping Voluson từ Server | Kiểm tra LAN cable |

### Vấn đề 2: Worklist trống (không có bệnh nhân)

**Triệu chứng:**
```
❌ No patients found
❌ Empty list
```

**Nguyên nhân & Cách khắc phục:**

| Nguyên nhân | Cách kiểm tra | Cách khắc phục |
|-----------|---------------|---------------|
| Chưa có appointments | `python check_system_health.py` | Thêm appointments vào hệ thống |
| Auto-sync chưa chạy | Check mwl.db timestamp | `python mwl_sync.py` |
| Service type sai | Kiểm tra "service_type" field | Đảm bảo chứa "siêu âm" hoặc "ultrasound" |
| Database lỗi | `sqlite3 clinic.db "PRAGMA integrity_check"` | Restore backup hoặc rebuild |

### Vấn đề 3: Slow Performance

**Triệu chứng:**
```
⚠️ Slow to load patients
⚠️ Timeout when querying
```

**Nguyên nhân & Cách khắc phục:**

| Nguyên nhân | Cách kiểm tra | Cách khắc phục |
|-----------|---------------|---------------|
| Database quá lớn | `du -h clinic.db` | Lưu trữ dữ liệu cũ riêng |
| Network slow | Ping -c 10 10.17.2.2 | Kiểm tra LAN connection |
| Server quá tải | Task manager - CPU/Memory | Restart MWL Server |
| Query complex | Check `mwl_sync.py` | Optimize database query |

### Vấn đề 4: DICOM Images không lưu

**Triệu chứng:**
```
❌ Cannot save DICOM images
❌ Export failed
```

**Nguyên nhân & Cách khắc phục:**

| Nguyên nhân | Cách kiểm tra | Cách khắc phục |
|-----------|---------------|---------------|
| Disk space full | `dir` trên Voluson | Xóa images cũ |
| Permission denied | Check folder permissions | Grant write permission |
| PACS connection | Check PACS settings | Verify PACS IP/port |

---

## 📊 BƯỚC 8: GIÁM SÁT & MAINTENANCE

### 8.1 Monitoring Hàng ngày

**Checklist:**
```bash
# 1. Kiểm tra MWL Server chạy
netstat -ano | findstr :104

# 2. Kiểm tra Database
python check_system_health.py

# 3. Kiểm tra Auto-sync
tail -f mwl_server.log

# 4. Kiểm tra Voluson connection
# Trực tiếp trên Voluson: DICOM → Test Connection
```

### 8.2 Backup Hàng tuần

**Backup databases:**

```bash
# Tạo folder backup
mkdir backup

# Backup clinic.db
copy clinic.db backup\clinic.db.$(date +%Y%m%d)

# Backup mwl.db
copy mwl.db backup\mwl.db.$(date +%Y%m%d)

# Verify backup
ls -la backup\
```

### 8.3 Log Review Hàng tháng

**Xem logs để phát hiện vấn đề:**

```bash
# View recent logs
tail -100 mwl_server.log

# Check for errors
grep -i "error" mwl_server.log | tail -20

# Check connection attempts
grep "C-FIND" mwl_server.log | tail -10
```

---

## 🎓 ADVANCED CONFIGURATION

### 9.1 Multiple Modalities

Nếu muốn hỗ trợ nhiều loại máy siêu âm:

```python
# Trong mwl_server.py, chỉnh sửa:
ALLOWED_AE_TITLES = [
    'VOLUSON_E10',      # Máy 1
    'PHILIPS_US',       # Máy 2
    'GE_LOGIQ',         # Máy 3
    '*'                 # Cho phép bất kỳ
]
```

### 9.2 Custom Worklist Filtering

Để lọc appointments theo tiêu chí tùy chỉnh:

```python
# Trong mwl_sync.py, chỉnh sửa filter:
def is_ultrasound(service_type):
    if not service_type:
        return False
    s = service_type.lower()
    # Custom filters
    for kw in ['siêu âm', 'ultrasound', 'us', 'echo']:
        if kw in s:
            return True
    return False
```

### 9.3 Enable DICOM Send

Nếu Voluson muốn gửi images về server:

Cấu hình DICOM Storage SCP trên server (thêm mới):

```python
# Tạo file: dicom_storage_server.py
# Implements C-STORE receiver
# Receives DICOM images từ Voluson
```

---

## 📱 WORKFLOW EXAMPLE

### Ví dụ: Quy trình Siêu âm Thai

**Sáng 8:00 - Bệnh nhân đến:**
1. Lễ tân nhập appointment vào hệ thống
2. Chọn dịch vụ: "Siêu âm thai"
3. Đặt lịch cho 8:30 AM

**8:15 - Auto-sync chạy:**
1. Đọc appointment từ clinic.db
2. Tạo DICOM worklist entry
3. Lưu vào mwl.db

**8:25 - Bệnh nhân vào phòng siêu âm:**
1. Bác sĩ bật Voluson E10
2. Query worklist: "Siêu âm thai"
3. Voluson lấy danh sách bệnh nhân
4. Chọn bệnh nhân: "Nguyễn Thị Test"

**8:30-8:50 - Thực hiện siêu âm:**
1. Thực hiện quét, đo lường
2. Ghi nhận số đo (tuổi thai, vị trí...)
3. Chụp hình ảnh quan trọng
4. Thêm nhận xét, chẩn đoán

**8:50 - Lưu kết quả:**
1. Lưu DICOM images trên Voluson
2. Tạo report PDF
3. In ra giấy cho bệnh nhân

**Chiều 14:00 - Bác sĩ review:**
1. Đăng nhập hệ thống web (port 5000)
2. Xem kết quả siêu âm
3. Cập nhật ghi chú cuối cùng

---

## ✅ CHECKLIST HOÀN THÀNH

```
CÀI ĐẶT VOLUSON E10:
□ MWL Server chạy trên port 104
□ Database clinic.db & mwl.db OK
□ Auto-sync hoạt động (mỗi 5 phút)
□ Voluson IP: 10.17.2.1 ✅
□ Server IP: 10.17.2.2 ✅
□ Network ping OK ✅

CẤU HÌNH VOLUSON:
□ Vào DICOM Settings
□ Thêm server Phong_Kham_Dai_Anh
□ IP: 10.17.2.2, Port: 104
□ Local AE: VOLUSON_E10
□ Remote AE: CLINIC_SYSTEM
□ Lưu cấu hình

KIỂM TRA:
□ Test Connection từ Voluson ✅
□ Worklist hiển thị bệnh nhân ✅
□ Có thể load thông tin appointment ✅
□ Có thể lưu kết quả siêu âm ✅
□ Web admin hiển thị dữ liệu ✅

HOÀN THÀNH:
✅ Voluson E10 kết nối thành công
✅ Worklist đã cài đặt
✅ Sẵn sàng triển khai
```

---

## 📞 HỖTRỢ & LIÊN HỆ

**Nếu có vấn đề:**

1. **Kiểm tra logs:**
   ```bash
   tail -f mwl_server.log
   ```

2. **Chạy health check:**
   ```bash
   python check_system_health.py
   python check_mwl_services.py
   ```

3. **Restart MWL Server:**
   ```bash
   python mwl_server.py
   # hoặc
   Restart-Service PK_DaiAnh_MWL  # Nếu dùng Windows Service
   ```

4. **Xem hướng dẫn Voluson:**
   Tham khảo manual máy Voluson E10 hoặc liên hệ Philips support

---

## 📚 THAM KHẢO THÊM

**Tài liệu liên quan:**
- [QUICK_START_MWL_SERVICE_v2.md](QUICK_START_MWL_SERVICE_v2.md) - Quick start
- [SYSTEM_HEALTH_CHECK_REPORT.md](SYSTEM_HEALTH_CHECK_REPORT.md) - System status
- [mwl_server.py](mwl_server.py) - MWL Server source code
- [mwl_sync.py](mwl_sync.py) - Auto-sync script

**DICOM Standards:**
- DICOM Modality Worklist Service – Class User
- DICOM Network Communication Support for Message Exchange
- ISO/IEC 8824: Abstract Syntax Notation One (ASN.1)

---

## 🎯 KÊTLUẬN

Voluson E10 đã được cấu hình để kết nối với Worklist server thành công!

**Bây giờ bạn có thể:**
✅ Query danh sách bệnh nhân từ Worklist  
✅ Tự động load thông tin appointment  
✅ Thực hiện siêu âm  
✅ Lưu kết quả  
✅ Đồng bộ dữ liệu với hệ thống  

---

**Hướng dẫn này do:** Phòng Khám Đại Anh  
**Ngày cập nhật:** 11 November 2025  
**Phiên bản:** 1.0  

**Trạng thái:** ✅ READY FOR DEPLOYMENT
