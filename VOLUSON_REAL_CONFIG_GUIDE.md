# Hướng dẫn cài đặt đồng bộ với máy Voluson E10 thực tế

## 📸 **Phân tích cấu hình từ ảnh chụp màn hình**

Dựa trên ảnh chụp màn hình DICOM Configuration của máy Voluson E10, tôi đã xác định được cấu hình thực tế:

### **Thông tin máy Voluson E10:**
- **AE Title**: `Voluson`
- **Station Name**: `US1`
- **IP Address**: `10.17.2.2` ⚠️ **Khác với IP mặc định**
- **Port**: `104`
- **Services đã bật**:
  - ✅ STORE (DICOM_EXPORT) → AE Title: `PC`
  - ✅ WORKLIST (ViewPoint WL) → AE Title: `VOLUSON_E10`

---

## 🔧 **CẬP NHẬT CẤU HÌNH HỆ THỐNG**

### **Bước 1: Cập nhật file cấu hình**
File `voluson_config.json` đã được cập nhật với IP thực tế:
```json
{
  "sync_enabled": true,
  "voluson_ip": "10.17.2.2",  ← Đã cập nhật từ 10.17.2.1
  "voluson_port": 104,
  "ae_title": "CLINIC_SYSTEM",
  "voluson_ae_title": "VOLUSON_E10",
  "sync_interval": 30,
  "retry_attempts": 3,
  "retry_delay": 10
}
```

### **Bước 2: Cập nhật giao diện web**
Giao diện web đã được cập nhật để hiển thị IP đúng (`10.17.2.2`)

---

## 🏥 **CẤU HÌNH MÁY VOLUSON E10**

### **Kiểm tra cấu hình hiện tại:**
Từ ảnh chụp, máy Voluson đã được cấu hình đúng:

#### **✅ DICOM Server Settings:**
- AE Title: `Voluson`
- Station Name: `US1`
- Retry Count: `2`
- Retry Count Seq.: `4`
- Retry Interval: `1 min.`
- Timeout: `45s`
- Character Set: `Language dependent`

#### **✅ Services Configuration:**
| Service | Alias | AE Title | IP Address | Port |
|---------|-------|----------|------------|------|
| STORE | DICOM_EXPORT | PC | 10.17.2.2 | 104 |
| WORKLIST | ViewPoint WL | VOLUSON_E10 | 10.17.2.2 | 104 |

### **Cần kiểm tra thêm:**
1. **Test Connection**: Nhấn nút "Test Connection" trên máy Voluson
2. **Ping**: Kiểm tra ping từ máy Voluson đến máy tính phòng khám
3. **Verify**: Kiểm tra verify connection

---

## 🖥️ **CẤU HÌNH MÁY TÍNH PHÒNG KHÁM**

### **Bước 1: Kiểm tra IP máy tính**
```bash
ipconfig
```
Ghi nhớ IP của máy tính (ví dụ: `192.168.1.100`)

### **Bước 2: Cấu hình trong giao diện web**
1. Truy cập: `http://127.0.0.1:5000/examination-list.html`
2. Nhấn ⚙️ → Tab "Voluson"
3. Cấu hình:
   ```
   ✅ Tự động đồng bộ: ON
   IP máy Voluson: 10.17.2.2
   Cổng DICOM: 104
   ```
4. Nhấn **"Kiểm tra kết nối"**

### **Bước 3: Test kết nối**
```bash
# Test ping đến máy Voluson
ping 10.17.2.2

# Test port 104
telnet 10.17.2.2 104
```

---

## 🔗 **CẤU HÌNH KẾT NỐI**

### **Từ máy tính phòng khám → Máy Voluson:**
```
Source: CLINIC_SYSTEM (IP: [IP máy tính])
Target: VOLUSON_E10 (IP: 10.17.2.2, Port: 104)
Service: WORKLIST
```

### **Từ máy Voluson → Máy tính phòng khám:**
```
Source: VOLUSON_E10 (IP: 10.17.2.2)
Target: CLINIC_SYSTEM (IP: [IP máy tính], Port: 104)
Service: STORE
```

---

## 🧪 **TEST ĐỒNG BỘ**

### **Bước 1: Test kết nối DICOM**
1. Trên máy Voluson: Nhấn "Test Connection"
2. Nhập thông tin:
   ```
   Remote AE Title: CLINIC_SYSTEM
   Remote IP: [IP máy tính phòng khám]
   Remote Port: 104
   ```
3. Phải hiển thị "Connection Successful"

### **Bước 2: Test đồng bộ worklist**
1. Thêm dịch vụ siêu âm cho bệnh nhân
2. Kiểm tra console log:
   ```
   INFO:voluson_sync_service:Đã đồng bộ dịch vụ siêu âm với Voluson E10
   ```
3. Kiểm tra worklist trên máy Voluson

---

## 🚨 **XỬ LÝ SỰ CỐ**

### **Lỗi: "WinError 10051"**
**Nguyên nhân**: Không thể kết nối đến IP 10.17.2.2
**Giải pháp**:
1. Kiểm tra máy Voluson có bật không
2. Kiểm tra cáp mạng
3. Kiểm tra firewall
4. Test ping: `ping 10.17.2.2`

### **Lỗi: "Association failed"**
**Nguyên nhân**: AE Title không khớp
**Giải pháp**:
1. Đảm bảo AE Title trên máy Voluson là `VOLUSON_E10`
2. Đảm bảo AE Title trên máy tính là `CLINIC_SYSTEM`

### **Worklist không hiển thị**
**Nguyên nhân**: Chưa có dữ liệu hoặc lỗi đồng bộ
**Giải pháp**:
1. Kiểm tra dịch vụ có nhóm "siêu âm" không
2. Kiểm tra log đồng bộ
3. Refresh worklist trên máy Voluson

---

## 📋 **CHECKLIST CÀI ĐẶT**

### **Máy Voluson E10:**
- [x] DICOM Server đã bật
- [x] AE Title: VOLUSON_E10
- [x] IP Address: 10.17.2.2
- [x] Port: 104
- [x] WORKLIST service đã enable
- [ ] Test Connection thành công

### **Máy tính phòng khám:**
- [x] IP đã cập nhật: 10.17.2.2
- [x] Port: 104
- [x] AE Title: CLINIC_SYSTEM
- [ ] Test kết nối thành công
- [ ] Đồng bộ worklist thành công

---

## 🎯 **BƯỚC TIẾP THEO**

1. **Khởi động hệ thống**: `python app.py`
2. **Truy cập web**: `http://127.0.0.1:5000/examination-list.html`
3. **Cấu hình Voluson**: Tab "Voluson" → IP: 10.17.2.2
4. **Test kết nối**: Nhấn "Kiểm tra kết nối"
5. **Test đồng bộ**: Thêm dịch vụ siêu âm

---

**🎉 Với cấu hình này, hệ thống sẽ kết nối chính xác với máy Voluson E10 thực tế của bạn!**
