# 🔄 HƯỚNG DẪN ĐỒNG BỘ WORKLIST VỚI VOLUSON E10

## ✅ ĐÃ SẴN SÀNG

### 1. ✅ Kiểm Tra Dữ Liệu
- **Database**: Đã có 7 appointments siêu âm
- **Các trường DICOM**: Đầy đủ 100%
- **Mapping**: Hoàn chỉnh

### 2. ✅ DICOM MWL Server
- **File**: `dicom_mwl_server.py`
- **Port**: 104
- **AE Title**: CLINIC_SYSTEM
- **Status**: Sẵn sàng chạy

### 3. ✅ Cấu Hình Network
- **Clinic PC**: 10.17.2.2 ✅
- **Voluson E10**: 10.17.2.1 ✅
- **Connection**: Đã test thành công ✅

---

## 🚀 CÁCH KHỞI ĐỘNG

### Phương án 1: Dùng Batch File (Windows)
```bash
start_all_servers.bat
```

### Phương án 2: Chạy Thủ Công

**Terminal 1** (Web Server):
```bash
python app.py
```

**Terminal 2** (DICOM MWL Server):
```bash
python dicom_mwl_server.py
```

---

## ⚙️ CẤU HÌNH TRÊN VOLUSON E10

### Bước 1: Vào DICOM Configuration
1. Mở menu chính trên Voluson E10
2. Chọn **Settings** → **DICOM Configuration**

### Bước 2: Add Destination
1. Chọn tab **Network** hoặc **SCP**
2. Nhấn **Add** hoặc **New**
3. Điền thông tin:
   - **AE Title**: `CLINIC_SYSTEM`
   - **Host**: `10.17.2.2`
   - **Port**: `104`

### Bước 3: Enable MWL (Modality Worklist)
1. Tìm mục **Worklist** hoặc **MWL Query**
2. Bật chức năng **Query Worklist**
3. Chọn `CLINIC_SYSTEM` làm MWL Server

### Bước 4: Test Connection
1. Nhấn **Test** hoặc **Verify**
2. Kỳ vọng:
   - ✅ **Ping**: OK
   - ✅ **Verify**: OK (Success)

---

## 🧪 TEST WORKLIST

### Trên Voluson E10:

1. **Query Worklist**:
   - Vào menu **Patients** hoặc **Worklist**
   - Chọn **Query Worklist** hoặc **MWL Query**
   - Chọn server `CLINIC_SYSTEM`
   - Nhấn **Query** hoặc **Refresh**

2. **Kỳ vọng**:
   - Danh sách worklist hiển thị
   - Có 7 appointments siêu âm
   - Thông tin: Tên bệnh nhân, ngày hẹn, dịch vụ...

---

## 📊 KIỂM TRA DỮ LIỆU

### Chạy script kiểm tra:
```bash
python check_worklist_fields.py
```

**Kết quả kỳ vọng**:
- ✅ Đủ các bảng
- ✅ Có dữ liệu siêu âm
- ✅ Mapping đầy đủ

---

## 🐛 TROUBLESHOOTING

### Lỗi 1: Không kết nối được
**Triệu chứng**: Ping Failed hoặc Verify Failed

**Giải pháp**:
1. Kiểm tra firewall:
   ```powershell
   # Cho phép port 104
   New-NetFirewallRule -DisplayName "DICOM MWL" -Direction Inbound -LocalPort 104 -Protocol TCP -Action Allow
   ```

2. Kiểm tra network:
   ```powershell
   Test-NetConnection -ComputerName 10.17.2.1 -Port 104
   ```

3. Kiểm tra DICOM server đang chạy:
   ```powershell
   netstat -ano | findstr 104
   ```

### Lỗi 2: Worklist trống
**Triệu chứng**: Query worklist không hiển thị gì

**Giải pháp**:
1. Kiểm tra database có dữ liệu:
   ```bash
   python check_worklist_fields.py
   ```

2. Xem logs của DICOM server:
   - Terminal chạy `dicom_mwl_server.py`
   - Tìm dòng `Nhận được C-FIND từ...`

3. Kiểm tra filter trên Voluson:
   - Đảm bảo không filter quá chặt
   - Thử query all dates

### Lỗi 3: Association Aborted
**Triệu chứng**: Verify Failed với lỗi Association Aborted

**Nguyên nhân**: DICOM Presentation Context không khớp

**Giải pháp**: Đã fix trong `dicom_mwl_server.py`
- ✅ Đã thêm `VerificationSOPClass`
- ✅ Đã thêm `ModalityWorklistInformationFind`

---

## 📝 DỮ LIỆU WORKLIST MẪU

Khi query thành công, Voluson E10 sẽ nhận được:

```
Patient ID: PAT_11
Patient Name: hà ngọc đại
Patient Birth Date: 19851111
Modality: US
Procedure: siêu âm thai 12-14 tuần
Date: 20251030
Time: 225800
Doctor: PK Đại Anh
Institution: Phòng khám chuyên khoa Phụ Sản Đại Anh
```

---

## ✅ CHECKLIST CUỐI CÙNG

Trước khi test trên Voluson E10, đảm bảo:

- [ ] Web server đang chạy (port 5000)
- [ ] DICOM MWL server đang chạy (port 104)
- [ ] Network có thể ping được cả 2 máy
- [ ] Port 104 không bị firewall chặn
- [ ] Voluson E10 đã cấu hình đúng AE Title
- [ ] Voluson E10 đã enable Query Worklist
- [ ] Database có dữ liệu siêu âm

---

## 🎯 KẾT QUẢ MONG ĐỢI

Sau khi hoàn tất:

1. **Trên Voluson E10**:
   - Test Connection: ✅ Success
   - Query Worklist: ✅ Có danh sách
   - Mỗi khi thêm appointment siêu âm trên web → Tự động hiện trên Voluson E10

2. **Trên Web**:
   - Thêm appointment siêu âm
   - Chọn dịch vụ siêu âm
   - Tự động sync lên Voluson E10

---

## 📞 HỖ TRỢ

Nếu còn vấn đề, kiểm tra:
1. `FIXED_AND_READY.md` - Trạng thái hệ thống
2. `WORKLIST_DATA_READY.md` - Kiểm tra dữ liệu
3. `VOLUSON_CORRECTED_IP_GUIDE.md` - Cấu hình IP
4. Logs trong terminal chạy `dicom_mwl_server.py`

---

**🎉 CHÚC THÀNH CÔNG! 🎉**

