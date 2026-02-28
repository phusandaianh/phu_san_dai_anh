# Hướng dẫn cấu hình đồng bộ Voluson E10 - IP đã cập nhật

## 🌐 **Cấu hình mạng chính xác:**

### **Thông tin IP đã được sửa:**
- **Máy tính phòng khám**: `10.17.2.2`
- **Máy Voluson E10**: `10.17.2.1`
- **Subnet**: `10.17.2.0/24`
- **Subnet Mask**: `255.255.255.0`

---

## 🔧 **CẤU HÌNH ĐÃ CẬP NHẬT**

### **File cấu hình hệ thống:**
```json
{
  "sync_enabled": true,
  "voluson_ip": "10.17.2.1",  ← Đã cập nhật
  "voluson_port": 104,
  "ae_title": "CLINIC_SYSTEM",
  "voluson_ae_title": "VOLUSON_E10"
}
```

### **Giao diện web:**
- IP máy Voluson hiển thị: `10.17.2.1`
- Giá trị mặc định đã cập nhật

---

## 🧪 **TEST KẾT NỐI VỚI IP MỚI**

### **Bước 1: Test ping từ máy tính đến Voluson**
```bash
ping 10.17.2.1
```
**Kết quả mong đợi:**
```
Pinging 10.17.2.1 with 32 bytes of data:
Reply from 10.17.2.1: bytes=32 time<1ms TTL=64
Reply from 10.17.2.1: bytes=32 time<1ms TTL=64
Reply from 10.17.2.1: bytes=32 time<1ms TTL=64
Reply from 10.17.2.1: bytes=32 time<1ms TTL=64
```

### **Bước 2: Test port DICOM**
```bash
telnet 10.17.2.1 104
```
**Kết quả mong đợi:** Kết nối thành công

### **Bước 3: Test từ giao diện web**
1. Truy cập: `http://127.0.0.1:5000/examination-list.html`
2. Nhấn ⚙️ → Tab "Voluson"
3. IP sẽ hiển thị: `10.17.2.1`
4. Nhấn **"Kiểm tra kết nối"**

---

## 🏥 **CẤU HÌNH MÁY VOLUSON E10**

### **Kiểm tra cấu hình DICOM trên Voluson:**
1. Vào **DICOM Configuration**
2. Đảm bảo:
   ```
   AE Title: VOLUSON_E10
   IP Address: 10.17.2.1
   Port: 104
   WORKLIST Service: ENABLED
   ```

### **Test kết nối từ Voluson:**
1. Nhấn **"Test Connection"**
2. Nhập thông tin:
   ```
   Remote AE Title: CLINIC_SYSTEM
   Remote IP: 10.17.2.2
   Remote Port: 104
   ```
3. Nhấn **Test**

---

## 🔗 **SƠ ĐỒ KẾT NỐI**

```
Mạng LAN: 10.17.2.0/24
├── Máy tính phòng khám: 10.17.2.2
│   ├── AE Title: CLINIC_SYSTEM
│   ├── Port: 104 (DICOM Client)
│   └── Gửi worklist → Voluson
│
└── Máy Voluson E10: 10.17.2.1
    ├── AE Title: VOLUSON_E10
    ├── Port: 104 (DICOM Server)
    └── Nhận worklist từ phòng khám
```

---

## 🚨 **XỬ LÝ SỰ CỐ VỚI IP MỚI**

### **Lỗi: "WinError 10051"**
**Nguyên nhân**: Không thể kết nối đến 10.17.2.1
**Giải pháp**:
1. **Kiểm tra máy Voluson**:
   - Đảm bảo IP là 10.17.2.1
   - Kiểm tra máy đã bật chưa
   - Kiểm tra cáp mạng

2. **Kiểm tra mạng**:
   ```bash
   # Test ping
   ping 10.17.2.1
   
   # Kiểm tra routing
   tracert 10.17.2.1
   ```

3. **Kiểm tra IP máy tính**:
   ```bash
   ipconfig
   # Phải hiển thị: 10.17.2.2
   ```

### **Lỗi: "Association failed"**
**Nguyên nhân**: AE Title hoặc IP không khớp
**Giải pháp**:
1. Đảm bảo AE Title trên Voluson là `VOLUSON_E10`
2. Đảm bảo AE Title trên máy tính là `CLINIC_SYSTEM`
3. Kiểm tra IP: Voluson = 10.17.2.1, Máy tính = 10.17.2.2

---

## 📊 **KIỂM TRA LOG VỚI IP MỚI**

### **Log mong đợi khi thành công:**
```
INFO:voluson_sync_service:Testing connection to Voluson E10 at 10.17.2.1:104
INFO:pynetdicom.assoc:Requesting Association
INFO:pynetdicom.assoc:Association accepted
INFO:voluson_sync_service:Connection test successful
```

### **Log lỗi cần kiểm tra:**
```
ERROR:pynetdicom.transport:TCP Initialisation Error: [WinError 10051]
# → Kiểm tra IP 10.17.2.1 có đúng không

ERROR:voluson_sync_service:Không thể kết nối đến Voluson E10
# → Kiểm tra máy Voluson có bật không
```

---

## 🎯 **TEST ĐỒNG BỘ HOÀN CHỈNH**

### **Bước 1: Khởi động hệ thống**
```bash
python app.py
```

### **Bước 2: Cấu hình trong web**
1. Truy cập: `http://127.0.0.1:5000/examination-list.html`
2. Nhấn ⚙️ → Tab "Voluson"
3. IP sẽ hiển thị: `10.17.2.1`
4. Nhấn **"Kiểm tra kết nối"**

### **Bước 3: Test đồng bộ**
1. Thêm dịch vụ siêu âm cho bệnh nhân
2. Kiểm tra log:
   ```
   INFO:voluson_sync_service:Đã đồng bộ dịch vụ siêu âm với Voluson E10
   ```
3. Kiểm tra worklist trên máy Voluson

---

## 📋 **CHECKLIST VỚI IP MỚI**

### **Mạng:**
- [x] Máy tính: 10.17.2.2
- [x] Voluson: 10.17.2.1
- [x] Cùng subnet: 10.17.2.0/24
- [ ] Ping 10.17.2.1 thành công
- [ ] Port 104 mở

### **DICOM:**
- [x] AE Title Voluson: VOLUSON_E10
- [x] AE Title Phòng khám: CLINIC_SYSTEM
- [x] Port: 104
- [ ] Test connection thành công

### **Đồng bộ:**
- [ ] Dịch vụ siêu âm được thêm
- [ ] Log đồng bộ thành công
- [ ] Worklist hiển thị đúng

---

**🎉 Với cấu hình IP mới này, hệ thống sẽ kết nối chính xác!**

**Hãy test kết nối và cho tôi biết kết quả nhé!** 🚀
