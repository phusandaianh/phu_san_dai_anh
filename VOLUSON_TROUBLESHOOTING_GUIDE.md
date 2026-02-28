# Hướng dẫn khắc phục lỗi kết nối Voluson E10

## 🚨 **Lỗi hiện tại: "Không thể kết nối đến máy Voluson E10"**

### **Từ ảnh chụp màn hình, tôi thấy:**
- ✅ IP đã đúng: `10.17.2.1`
- ✅ Port đã đúng: `104`
- ✅ Checkbox đồng bộ đã bật
- ❌ **Lỗi kết nối**: Hộp đỏ hiển thị lỗi

---

## 🔧 **CÁC BƯỚC KHẮC PHỤC**

### **Bước 1: Chạy script debug**
```bash
python voluson_debug.py
```
Script này sẽ kiểm tra:
- Ping đến máy Voluson
- Kết nối TCP port 104
- Kết nối DICOM
- Cấu hình mạng
- Trạng thái firewall

### **Bước 2: Kiểm tra máy Voluson E10**

#### **2.1 Kiểm tra máy có bật không:**
- Đảm bảo máy Voluson E10 đã khởi động
- Kiểm tra đèn mạng có sáng không
- Kiểm tra màn hình có hiển thị không

#### **2.2 Kiểm tra cấu hình DICOM:**
1. Vào **DICOM Configuration** trên máy Voluson
2. Kiểm tra:
   ```
   AE Title: VOLUSON_E10
   IP Address: 10.17.2.1
   Port: 104
   DICOM Server: ENABLED
   WORKLIST Service: ENABLED
   ```

#### **2.3 Test kết nối từ Voluson:**
1. Nhấn **"Test Connection"**
2. Nhập:
   ```
   Remote AE Title: CLINIC_SYSTEM
   Remote IP: 10.17.2.2
   Remote Port: 104
   ```
3. Nhấn **Test**

### **Bước 3: Kiểm tra mạng**

#### **3.1 Test ping từ máy tính:**
```bash
ping 10.17.2.1
```
**Kết quả mong đợi:**
```
Pinging 10.17.2.1 with 32 bytes of data:
Reply from 10.17.2.1: bytes=32 time<1ms TTL=64
```

#### **3.2 Test port DICOM:**
```bash
telnet 10.17.2.1 104
```
**Kết quả mong đợi:** Kết nối thành công (không có lỗi)

#### **3.3 Kiểm tra IP máy tính:**
```bash
ipconfig
```
**Phải hiển thị:** `10.17.2.2`

### **Bước 4: Kiểm tra firewall**

#### **4.1 Tắt Windows Firewall tạm thời:**
1. Mở **Windows Defender Firewall**
2. Nhấn **"Turn Windows Defender Firewall on or off"**
3. Tắt **Private network** và **Public network**
4. Test kết nối lại

#### **4.2 Mở port 104:**
```bash
netsh advfirewall firewall add rule name="DICOM Port 104" dir=in action=allow protocol=TCP localport=104
```

### **Bước 5: Kiểm tra DICOM service**

#### **5.1 Restart DICOM service trên Voluson:**
1. Vào **System Services**
2. Tìm **DICOM Service**
3. Nhấn **Stop** → **Start**

#### **5.2 Kiểm tra log DICOM:**
1. Vào **System Logs** → **DICOM Logs**
2. Tìm các lỗi:
   - `Association failed`
   - `Connection timeout`
   - `Authentication failed`

---

## 🔍 **DEBUG CHI TIẾT**

### **Lỗi thường gặp và cách khắc phục:**

#### **1. "WinError 10051: A socket operation was attempted to an unreachable network"**
**Nguyên nhân**: Không thể kết nối đến IP
**Giải pháp**:
- Kiểm tra máy Voluson có bật không
- Kiểm tra IP có đúng không
- Kiểm tra cáp mạng

#### **2. "Association request failed: unable to connect to remote"**
**Nguyên nhân**: Port 104 bị chặn hoặc DICOM service tắt
**Giải pháp**:
- Kiểm tra firewall
- Kiểm tra DICOM service trên Voluson
- Mở port 104

#### **3. "Association request failed: unable to connect to remote"**
**Nguyên nhân**: AE Title không khớp
**Giải pháp**:
- Đảm bảo AE Title trên Voluson là `VOLUSON_E10`
- Đảm bảo AE Title trên máy tính là `CLINIC_SYSTEM`

---

## 🧪 **TEST TỪNG BƯỚC**

### **Test 1: Ping**
```bash
ping 10.17.2.1
```
**Nếu thành công**: Chuyển Test 2
**Nếu thất bại**: Kiểm tra máy Voluson và mạng

### **Test 2: Port**
```bash
telnet 10.17.2.1 104
```
**Nếu thành công**: Chuyển Test 3
**Nếu thất bại**: Kiểm tra firewall và DICOM service

### **Test 3: DICOM**
```bash
python voluson_debug.py
```
**Nếu thành công**: Kết nối hoạt động
**Nếu thất bại**: Kiểm tra AE Title và cấu hình DICOM

---

## 📋 **CHECKLIST KHẮC PHỤC**

### **Máy Voluson E10:**
- [ ] Máy đã bật
- [ ] IP: 10.17.2.1
- [ ] DICOM Server: ENABLED
- [ ] WORKLIST: ENABLED
- [ ] AE Title: VOLUSON_E10
- [ ] Test connection thành công

### **Máy tính phòng khám:**
- [ ] IP: 10.17.2.2
- [ ] Ping 10.17.2.1 thành công
- [ ] Port 104 mở
- [ ] Firewall không chặn
- [ ] DICOM libraries cài đặt

### **Mạng:**
- [ ] Cáp mạng kết nối tốt
- [ ] Cùng subnet: 10.17.2.0/24
- [ ] Không có router chặn
- [ ] Không có antivirus chặn

---

## 🎯 **SAU KHI KHẮC PHỤC**

### **Test kết nối từ web:**
1. Truy cập: `http://127.0.0.1:5000/examination-list.html`
2. Nhấn ⚙️ → Tab "Voluson"
3. Nhấn **"Kiểm tra kết nối"**
4. Phải hiển thị: **"Kết nối thành công"** (màu xanh)

### **Test đồng bộ:**
1. Thêm dịch vụ siêu âm cho bệnh nhân
2. Kiểm tra log: `INFO:voluson_sync_service:Đã đồng bộ...`
3. Kiểm tra worklist trên máy Voluson

---

**🔧 Hãy chạy script debug và cho tôi biết kết quả để tôi giúp bạn khắc phục cụ thể!**
