# Hướng dẫn test kết nối Voluson E10 với cấu hình mạng thực tế

## 🌐 **Cấu hình mạng đã xác định:**

### **Máy tính phòng khám:**
- **IP**: `10.17.2.1`
- **Subnet**: `255.255.255.0`
- **Gateway**: Không có
- **DNS**: `8.8.8.8`, `8.8.4.4`

### **Máy Voluson E10:**
- **IP**: `10.17.2.2`
- **Port**: `104`
- **AE Title**: `VOLUSON_E10`

---

## 🧪 **TEST KẾT NỐI**

### **Bước 1: Test ping từ máy tính đến Voluson**
```bash
ping 10.17.2.2
```
**Kết quả mong đợi:**
```
Pinging 10.17.2.2 with 32 bytes of data:
Reply from 10.17.2.2: bytes=32 time<1ms TTL=64
Reply from 10.17.2.2: bytes=32 time<1ms TTL=64
Reply from 10.17.2.2: bytes=32 time<1ms TTL=64
Reply from 10.17.2.2: bytes=32 time<1ms TTL=64
```

### **Bước 2: Test port DICOM**
```bash
telnet 10.17.2.2 104
```
**Kết quả mong đợi:** Kết nối thành công (không có lỗi)

### **Bước 3: Test từ giao diện web**
1. Truy cập: `http://127.0.0.1:5000/examination-list.html`
2. Nhấn ⚙️ → Tab "Voluson"
3. Cấu hình:
   ```
   IP máy Voluson: 10.17.2.2
   Cổng DICOM: 104
   ```
4. Nhấn **"Kiểm tra kết nối"**

---

## 🔧 **CẤU HÌNH MÁY VOLUSON E10**

### **Kiểm tra trên máy Voluson:**
1. Vào **DICOM Configuration**
2. Nhấn **"Test Connection"**
3. Nhập thông tin:
   ```
   Remote AE Title: CLINIC_SYSTEM
   Remote IP: 10.17.2.1
   Remote Port: 104
   ```
4. Nhấn **Test**

### **Cấu hình WORKLIST:**
Đảm bảo trên máy Voluson có:
```
Service: WORKLIST
Alias: ViewPoint WL
AE Title: VOLUSON_E10
IP Address: 10.17.2.2
Port: 104
Status: ENABLED
```

---

## 🚨 **XỬ LÝ SỰ CỐ**

### **Lỗi: "WinError 10051"**
**Nguyên nhân**: Không thể kết nối đến 10.17.2.2
**Giải pháp**:
1. **Kiểm tra máy Voluson**:
   - Đảm bảo máy đã bật
   - Kiểm tra đèn mạng
   - Kiểm tra cáp mạng

2. **Kiểm tra mạng**:
   ```bash
   # Test ping
   ping 10.17.2.2
   
   # Kiểm tra routing
   tracert 10.17.2.2
   ```

3. **Kiểm tra firewall**:
   - Tắt Windows Firewall tạm thời
   - Kiểm tra antivirus

### **Lỗi: "Association failed"**
**Nguyên nhân**: AE Title không khớp
**Giải pháp**:
1. Đảm bảo AE Title trên Voluson là `VOLUSON_E10`
2. Đảm bảo AE Title trên máy tính là `CLINIC_SYSTEM`

### **Lỗi: "Port 104 blocked"**
**Nguyên nhân**: Firewall chặn port
**Giải pháp**:
```bash
# Mở port 104 trên Windows Firewall
netsh advfirewall firewall add rule name="DICOM Port 104" dir=in action=allow protocol=TCP localport=104
```

---

## 📊 **KIỂM TRA LOG**

### **Xem log hệ thống:**
```bash
# Xem log real-time
tail -f voluson_sync.log

# Xem log lỗi
grep "ERROR" voluson_sync.log
```

### **Log mong đợi khi thành công:**
```
INFO:voluson_sync_service:Testing connection to Voluson E10 at 10.17.2.2:104
INFO:pynetdicom.assoc:Requesting Association
INFO:pynetdicom.assoc:Association accepted
INFO:voluson_sync_service:Connection test successful
```

---

## 🎯 **TEST ĐỒNG BỘ HOÀN CHỈNH**

### **Bước 1: Tạo dịch vụ siêu âm**
1. Vào danh sách khám
2. Chọn bệnh nhân
3. Nhấn "Thêm dịch vụ"
4. Chọn dịch vụ có nhóm "siêu âm"

### **Bước 2: Kiểm tra đồng bộ**
1. Xem console log:
   ```
   INFO:voluson_sync_service:Đã đồng bộ dịch vụ siêu âm với Voluson E10
   ```

2. Kiểm tra worklist trên máy Voluson:
   - Vào **Worklist**
   - Tìm thông tin bệnh nhân vừa thêm
   - Kiểm tra thông tin có đầy đủ không

### **Bước 3: Xác nhận thành công**
- ✅ Log không có lỗi
- ✅ Worklist hiển thị đúng
- ✅ Thông tin bệnh nhân chính xác

---

## 📋 **CHECKLIST CUỐI CÙNG**

### **Mạng:**
- [x] Máy tính: 10.17.2.1
- [x] Voluson: 10.17.2.2
- [x] Cùng subnet: 10.17.2.0/24
- [ ] Ping thành công
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

**🎉 Với cấu hình mạng này, hệ thống sẽ hoạt động hoàn hảo!**
