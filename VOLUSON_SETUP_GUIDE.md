# Hướng dẫn cài đặt đồng bộ Voluson E10

## 📋 **Tổng quan**
Hướng dẫn này sẽ giúp bạn cài đặt và cấu hình đồng bộ giữa hệ thống phòng khám và máy siêu âm Voluson E10 thông qua giao thức DICOM.

---

## 🖥️ **PHẦN 1: Cài đặt trên máy tính phòng khám**

### **Bước 1.1: Kiểm tra yêu cầu hệ thống**
- **Hệ điều hành**: Windows 10/11
- **Python**: 3.8 trở lên
- **RAM**: Tối thiểu 4GB
- **Ổ cứng**: 2GB trống
- **Mạng**: Kết nối mạng LAN với máy Voluson E10

### **Bước 1.2: Cài đặt Python packages**
Mở Command Prompt với quyền Administrator và chạy:

```bash
# Cài đặt các thư viện cần thiết
pip install pydicom==2.3.0
pip install pynetdicom==2.0.0
pip install flask==2.0.1
pip install flask-sqlalchemy==2.5.1

# Kiểm tra cài đặt
python -c "import pydicom, pynetdicom; print('DICOM libraries installed successfully')"
```

### **Bước 1.3: Cấu hình mạng**
1. **Kiểm tra IP máy tính**:
   ```bash
   ipconfig
   ```
   Ghi nhớ địa chỉ IP (ví dụ: 192.168.1.100)

2. **Test kết nối với máy Voluson**:
   ```bash
   ping 10.17.2.1
   ```

### **Bước 1.4: Cấu hình firewall**
1. Mở **Windows Defender Firewall**
2. Chọn **"Allow an app or feature through Windows Defender Firewall"**
3. Nhấn **"Change settings"** → **"Allow another app..."**
4. Thêm **Python.exe** và **Command Prompt**
5. Đảm bảo cả **Private** và **Public** đều được check

---

## 🏥 **PHẦN 2: Cài đặt trên máy Voluson E10**

### **Bước 2.1: Truy cập cài đặt DICOM**
1. **Khởi động máy Voluson E10**
2. Đăng nhập với tài khoản **Administrator**
3. Vào **Settings** → **Network** → **DICOM**

### **Bước 2.2: Cấu hình DICOM Server**
1. **Bật DICOM Server**:
   - ✅ Enable DICOM Server: **ON**
   - ✅ Enable MWL (Modality Worklist): **ON**
   - ✅ Enable Storage: **ON**

2. **Cấu hình thông số mạng**:
   ```
   AE Title: VOLUSON_E10
   IP Address: 10.17.2.1 (hoặc IP thực tế của máy)
   Port: 104
   ```

3. **Cấu hình Worklist**:
   ```
   Worklist AE Title: CLINIC_SYSTEM
   Worklist IP: [IP máy tính phòng khám]
   Worklist Port: 104
   ```

### **Bước 2.3: Cấu hình bảo mật**
1. **Authentication**: Disable (cho môi trường nội bộ)
2. **TLS**: Disable (cho môi trường nội bộ)
3. **Logging**: Enable (để debug)

### **Bước 2.4: Test DICOM Server**
1. Vào **DICOM** → **Test Connection**
2. Nhập thông tin:
   ```
   Remote AE Title: CLINIC_SYSTEM
   Remote IP: [IP máy tính phòng khám]
   Remote Port: 104
   ```
3. Nhấn **Test** → Phải hiển thị **"Connection Successful"**

---

## ⚙️ **PHẦN 3: Cấu hình hệ thống phòng khám**

### **Bước 3.1: Cấu hình file voluson_config.json**
Tạo file `voluson_config.json` trong thư mục gốc:

```json
{
  "sync_enabled": true,
  "voluson_ip": "10.17.2.1",
  "voluson_port": 104,
  "ae_title": "CLINIC_SYSTEM",
  "voluson_ae_title": "VOLUSON_E10",
  "sync_interval": 30,
  "retry_attempts": 3,
  "retry_delay": 10,
  "log_level": "INFO"
}
```

### **Bước 3.2: Cấu hình trong giao diện web**
1. Truy cập: `http://127.0.0.1:5000/examination-list.html`
2. Nhấn nút ⚙️ bên cạnh cột "Gọi"
3. Chọn tab **"Voluson"**
4. Cấu hình:
   ```
   ✅ Tự động đồng bộ: ON
   IP máy Voluson: 10.17.2.1
   Cổng DICOM: 104
   ```
5. Nhấn **"Kiểm tra kết nối"**
6. Nhấn **"Lưu"**

### **Bước 3.3: Test đồng bộ**
1. Thêm một dịch vụ siêu âm cho bệnh nhân
2. Kiểm tra console log:
   ```
   INFO:voluson_sync_service:Đã đồng bộ dịch vụ siêu âm 'Siêu âm thai' với Voluson E10
   ```
3. Kiểm tra worklist trên máy Voluson E10

---

## 🔧 **PHẦN 4: Xử lý sự cố**

### **Lỗi kết nối mạng**
**Triệu chứng**: `WinError 10051: A socket operation was attempted to an unreachable network`

**Giải pháp**:
1. **Kiểm tra IP**: Đảm bảo IP máy Voluson đúng
2. **Kiểm tra mạng**: Ping từ máy tính đến máy Voluson
3. **Kiểm tra firewall**: Tắt Windows Firewall tạm thời để test
4. **Kiểm tra cáp mạng**: Đảm bảo cáp mạng kết nối tốt

### **Lỗi DICOM Association**
**Triệu chứng**: `Association request failed: unable to connect to remote`

**Giải pháp**:
1. **Kiểm tra DICOM Server**: Đảm bảo DICOM Server đã bật trên Voluson
2. **Kiểm tra AE Title**: Đảm bảo AE Title khớp nhau
3. **Kiểm tra Port**: Đảm bảo Port 104 không bị chặn
4. **Restart DICOM Service**: Restart DICOM service trên Voluson

### **Lỗi Worklist không hiển thị**
**Triệu chứng**: Dữ liệu không xuất hiện trên worklist Voluson

**Giải pháp**:
1. **Kiểm tra MWL**: Đảm bảo MWL đã enable trên Voluson
2. **Kiểm tra thông tin bệnh nhân**: Đảm bảo thông tin đầy đủ
3. **Kiểm tra Modality**: Đảm bảo Modality = "US"
4. **Refresh Worklist**: Refresh worklist trên Voluson

---

## 📊 **PHẦN 5: Kiểm tra và giám sát**

### **Kiểm tra log hệ thống**
```bash
# Xem log real-time
tail -f voluson_sync.log

# Xem log lỗi
grep "ERROR" voluson_sync.log
```

### **Kiểm tra trạng thái đồng bộ**
1. Vào database SQLite:
   ```bash
   sqlite3 clinic.db
   ```
2. Kiểm tra appointments đã đồng bộ:
   ```sql
   SELECT id, patient_id, voluson_synced, voluson_sync_time 
   FROM appointment 
   WHERE voluson_synced = 1;
   ```

### **Test thủ công**
```python
# Test kết nối
from voluson_sync_service import get_voluson_sync_service
sync_service = get_voluson_sync_service()
success = sync_service.test_connection()
print(f"Connection test: {success}")
```

---

## 🚀 **PHẦN 6: Vận hành hàng ngày**

### **Quy trình sử dụng**
1. **Khởi động hệ thống**: Chạy `python app.py`
2. **Kiểm tra kết nối**: Test kết nối Voluson
3. **Thêm dịch vụ siêu âm**: Tự động đồng bộ
4. **Kiểm tra worklist**: Xác nhận trên máy Voluson
5. **Theo dõi log**: Kiểm tra lỗi nếu có

### **Bảo trì định kỳ**
- **Hàng ngày**: Kiểm tra log lỗi
- **Hàng tuần**: Test kết nối DICOM
- **Hàng tháng**: Backup cấu hình và database
- **Hàng quý**: Cập nhật phần mềm nếu có

---

## 📞 **Hỗ trợ kỹ thuật**

### **Thông tin liên hệ**
- **IT Support**: [Số điện thoại]
- **Email**: [Email hỗ trợ]
- **Documentation**: `VOLUSON_SYNC_GUIDE.md`

### **Thông tin hệ thống**
- **Version**: 1.0
- **Last Updated**: 28/10/2025
- **Compatible**: Voluson E10, E8, E6

---

## ✅ **Checklist cài đặt**

### **Máy tính phòng khám**
- [ ] Python packages đã cài đặt
- [ ] Firewall đã cấu hình
- [ ] IP mạng đã kiểm tra
- [ ] File config đã tạo
- [ ] Test kết nối thành công

### **Máy Voluson E10**
- [ ] DICOM Server đã bật
- [ ] MWL đã enable
- [ ] AE Title đã cấu hình
- [ ] IP/Port đã đúng
- [ ] Test connection thành công

### **Hệ thống tích hợp**
- [ ] Giao diện web đã cấu hình
- [ ] Test đồng bộ thành công
- [ ] Worklist hiển thị đúng
- [ ] Log không có lỗi
- [ ] Quy trình vận hành đã test

**🎉 Chúc mừng! Hệ thống đồng bộ Voluson E10 đã sẵn sàng hoạt động!**
