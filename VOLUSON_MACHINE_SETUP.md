# Hướng dẫn cấu hình máy Voluson E10

## 🏥 **CẤU HÌNH MÁY VOLUSON E10**

### **Bước 1: Truy cập cài đặt hệ thống**
1. **Khởi động máy Voluson E10**
2. **Đăng nhập** với tài khoản Administrator
3. Vào **System Settings** → **Network** → **DICOM**

### **Bước 2: Cấu hình DICOM Server**

#### **2.1 Bật DICOM Services**
```
✅ DICOM Server: ENABLED
✅ Modality Worklist (MWL): ENABLED  
✅ Storage Service: ENABLED
✅ Query/Retrieve: ENABLED
```

#### **2.2 Cấu hình thông số mạng**
```
AE Title: VOLUSON_E10
IP Address: 10.17.2.1 (hoặc IP thực tế của máy)
Port: 104
Max PDU Size: 16384
```

#### **2.3 Cấu hình Worklist**
```
Worklist AE Title: CLINIC_SYSTEM
Worklist IP: [IP máy tính phòng khám]
Worklist Port: 104
Worklist Query Interval: 30 seconds
```

### **Bước 3: Cấu hình bảo mật**

#### **3.1 Authentication**
```
DICOM Authentication: DISABLED (cho môi trường nội bộ)
User Authentication: DISABLED
```

#### **3.2 Encryption**
```
TLS Encryption: DISABLED (cho môi trường nội bộ)
SSL/TLS: DISABLED
```

#### **3.3 Logging**
```
DICOM Logging: ENABLED
Log Level: INFO
Log File: /var/log/dicom.log
```

### **Bước 4: Test kết nối**

#### **4.1 Test DICOM Server**
1. Vào **DICOM** → **Test Connection**
2. Nhập thông tin:
   ```
   Remote AE Title: CLINIC_SYSTEM
   Remote IP: [IP máy tính phòng khám]
   Remote Port: 104
   ```
3. Nhấn **Test**
4. Phải hiển thị **"Connection Successful"**

#### **4.2 Test Worklist**
1. Vào **Worklist** → **Test Query**
2. Kiểm tra có thể query worklist không
3. Phải hiển thị danh sách worklist items

### **Bước 5: Cấu hình nâng cao**

#### **5.1 Timeout Settings**
```
Association Timeout: 30 seconds
Connection Timeout: 10 seconds
Response Timeout: 60 seconds
```

#### **5.2 Retry Settings**
```
Max Retries: 3
Retry Delay: 5 seconds
```

#### **5.3 Worklist Settings**
```
Auto Refresh: ENABLED
Refresh Interval: 30 seconds
Max Worklist Items: 100
```

---

## 🔧 **KIỂM TRA VÀ XỬ LÝ SỰ CỐ**

### **Kiểm tra trạng thái DICOM**
1. Vào **System Status** → **DICOM Status**
2. Kiểm tra:
   - ✅ DICOM Server: RUNNING
   - ✅ MWL Service: RUNNING
   - ✅ Storage Service: RUNNING

### **Kiểm tra log**
1. Vào **System Logs** → **DICOM Logs**
2. Tìm các lỗi:
   - `Association failed`
   - `Connection timeout`
   - `Authentication failed`

### **Restart DICOM Service**
1. Vào **System Services** → **DICOM Service**
2. Nhấn **Stop** → **Start**
3. Kiểm tra trạng thái: **RUNNING**

---

## 📋 **CHECKLIST CẤU HÌNH VOLUSON**

### **DICOM Server**
- [ ] DICOM Server đã bật
- [ ] AE Title: VOLUSON_E10
- [ ] IP Address đã cấu hình đúng
- [ ] Port: 104
- [ ] Max PDU Size: 16384

### **Modality Worklist**
- [ ] MWL đã enable
- [ ] Worklist AE Title: CLINIC_SYSTEM
- [ ] Worklist IP đã cấu hình
- [ ] Worklist Port: 104
- [ ] Auto Refresh: ON

### **Bảo mật**
- [ ] Authentication: DISABLED
- [ ] TLS Encryption: DISABLED
- [ ] Logging: ENABLED

### **Test kết nối**
- [ ] Test DICOM Connection: SUCCESS
- [ ] Test Worklist Query: SUCCESS
- [ ] DICOM Service: RUNNING

---

## 🚨 **XỬ LÝ SỰ CỐ THƯỜNG GẶP**

### **Lỗi: "Association failed"**
**Nguyên nhân**: AE Title không khớp
**Giải pháp**: Kiểm tra AE Title trên cả hai máy

### **Lỗi: "Connection timeout"**
**Nguyên nhân**: Firewall chặn port 104
**Giải pháp**: Mở port 104 trên firewall

### **Lỗi: "Worklist empty"**
**Nguyên nhân**: Chưa có dữ liệu từ phòng khám
**Giải pháp**: Kiểm tra đồng bộ từ phòng khám

### **Lỗi: "DICOM Service not running"**
**Nguyên nhân**: Service bị tắt
**Giải pháp**: Restart DICOM Service

---

## 📞 **HỖ TRỢ KỸ THUẬT**

### **Thông tin máy Voluson**
- **Model**: Voluson E10
- **Software Version**: [Phiên bản hiện tại]
- **DICOM Version**: 3.0
- **Network**: Ethernet

### **Liên hệ hỗ trợ**
- **GE Healthcare Support**: [Số điện thoại]
- **Local IT Support**: [Số điện thoại]
- **Documentation**: Voluson E10 User Manual

---

**✅ Sau khi hoàn thành tất cả các bước trên, máy Voluson E10 đã sẵn sàng nhận dữ liệu từ hệ thống phòng khám!**
