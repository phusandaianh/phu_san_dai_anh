# Hướng dẫn sử dụng chức năng đồng bộ Voluson E10

## Tổng quan
Chức năng đồng bộ Voluson E10 cho phép tự động gửi thông tin bệnh nhân và dịch vụ siêu âm đến worklist của máy siêu âm Voluson E10 thông qua giao thức DICOM.

## Cài đặt và cấu hình

### 1. Cấu hình máy Voluson E10
- Đảm bảo máy Voluson E10 đã được cấu hình DICOM
- Ghi nhớ địa chỉ IP và cổng DICOM của máy
- Mặc định: IP `10.17.2.1`, Port `104`

### 2. Cấu hình hệ thống phòng khám
1. Truy cập trang `http://127.0.0.1:5000/examination-list.html`
2. Nhấn nút ⚙️ bên cạnh cột "Gọi"
3. Chọn tab **"Voluson"**
4. Cấu hình các thông số:
   - **IP máy Voluson**: Địa chỉ IP của máy siêu âm
   - **Cổng DICOM**: Cổng DICOM (mặc định 104)
   - **Bật đồng bộ**: Checkbox để enable/disable tự động đồng bộ

### 3. Test kết nối
1. Nhấn nút **"Kiểm tra kết nối"**
2. Hệ thống sẽ hiển thị trạng thái kết nối:
   - ✅ **Xanh**: Kết nối thành công
   - ❌ **Đỏ**: Lỗi kết nối
   - 🟡 **Vàng**: Đang kiểm tra

## Sử dụng chức năng

### Tự động đồng bộ khi thêm dịch vụ siêu âm

1. **Chọn bệnh nhân** trong danh sách khám
2. **Nhấn "Thêm dịch vụ"**
3. **Chọn dịch vụ siêu âm**:
   - Siêu âm thai
   - Siêu âm khác
   - Bất kỳ dịch vụ nào có nhóm chứa "siêu âm"
4. **Hệ thống tự động**:
   - Tạo DICOM worklist entry
   - Gửi thông tin đến máy Voluson E10
   - Đánh dấu appointment đã đồng bộ

### Thông tin được đồng bộ

#### Thông tin bệnh nhân:
- Tên bệnh nhân
- Ngày sinh
- Địa chỉ
- Số điện thoại

#### Thông tin cuộc hẹn:
- Ngày giờ khám
- Tên dịch vụ siêu âm
- Tên bác sĩ chỉ định
- ID cuộc hẹn

#### Thông tin cơ sở:
- Tên phòng khám: "Phòng khám chuyên khoa Phụ Sản Đại Anh"
- Địa chỉ: "TDP Quán Trắng - Tân An - Bắc Ninh"

## Kiểm tra và debug

### 1. Console Log
Mở Developer Tools (F12) → Console để xem log:
```
Đã đồng bộ dịch vụ siêu âm 'Siêu âm thai' với Voluson E10
```

### 2. Kiểm tra worklist trên máy Voluson
- Mở worklist trên máy Voluson E10
- Tìm thông tin bệnh nhân vừa được đồng bộ
- Kiểm tra thông tin có chính xác không

### 3. Trạng thái đồng bộ
- Các appointment đã đồng bộ sẽ được đánh dấu trong database
- Cột `voluson_synced` sẽ được set = 1

## Xử lý sự cố

### Lỗi kết nối
**Nguyên nhân:**
- IP hoặc Port không đúng
- Máy Voluson E10 không bật
- Firewall chặn kết nối
- Cấu hình DICOM không đúng

**Giải pháp:**
1. Kiểm tra IP và Port trên máy Voluson
2. Đảm bảo máy Voluson đang hoạt động
3. Kiểm tra firewall và network
4. Xác nhận cấu hình DICOM

### Lỗi đồng bộ
**Nguyên nhân:**
- Dịch vụ không thuộc nhóm siêu âm
- Thông tin bệnh nhân không đầy đủ
- Lỗi DICOM protocol

**Giải pháp:**
1. Kiểm tra `service_group` của dịch vụ
2. Đảm bảo thông tin bệnh nhân đầy đủ
3. Kiểm tra log để xem lỗi cụ thể

## Cấu hình nâng cao

### File cấu hình: `voluson_config.json`
```json
{
  "sync_enabled": true,
  "voluson_ip": "10.17.2.1",
  "voluson_port": 104,
  "ae_title": "CLINIC_SYSTEM",
  "voluson_ae_title": "VOLUSON_E10",
  "sync_interval": 30,
  "retry_attempts": 3,
  "retry_delay": 10
}
```

### API Endpoints
- `POST /api/test-voluson-connection`: Test kết nối
- `GET /api/voluson/config`: Lấy cấu hình
- `PUT /api/voluson/config`: Cập nhật cấu hình

## Lưu ý quan trọng

1. **Bảo mật**: Đảm bảo máy Voluson E10 trong mạng nội bộ an toàn
2. **Backup**: Thường xuyên backup cấu hình và database
3. **Monitoring**: Theo dõi log để phát hiện lỗi sớm
4. **Testing**: Test kết nối trước khi sử dụng trong production

## Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra log trong console
2. Test kết nối với máy Voluson
3. Xác nhận cấu hình DICOM
4. Liên hệ IT support nếu cần thiết