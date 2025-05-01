# Yêu cầu cho trang web đăng ký khám bệnh online - Phòng khám chuyên khoa Phụ Sản Đại Anh

## Thông tin cơ bản
- **Tên phòng khám:** Phòng khám chuyên khoa Phụ Sản Đại Anh
- **Số điện thoại:** 0858838616
- **Địa chỉ:** Làn 4, đối diện công ty may Unicoglobal. Tổ dân phố Quán Trắng - Phường Tân An - Thành phố Bắc Giang
- **Email quản trị:** phusandaianh@gmail.com

## Yêu cầu chức năng
1. **Giao diện đăng ký khám bệnh online**
   - Biểu mẫu đăng ký với các trường thông tin cần thiết
   - Xác nhận đăng ký và thông báo

2. **Thông tin phòng khám**
   - Hiển thị thông tin liên hệ
   - Tích hợp Google Maps với iframe được cung cấp
   - Ô địa chỉ website phòng khám
   - Quảng cáo dịch vụ: "Khám, quản lý thai nghén, siêu âm dị tật thai chuyên sâu 5D"
   - Slogan: "Uy Tín - Chất Lượng"
   - Ô truy cập lịch làm việc phòng khám

3. **Tính năng liên hệ**
   - Biểu tượng để liên hệ qua Zalo (kết nối với số điện thoại 0858838616)

## Yêu cầu thiết kế
1. **Màu sắc và giao diện**
   - Sử dụng màu xanh hài hòa
   - Có hiệu ứng động đẹp mắt
   - Giao diện thân thiện với người dùng

2. **Tích hợp Google Maps**
   - Iframe Google Maps:
   ```html
   <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3718.030146801113!2d106.25976408081718!3d21.270274229026402!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x31350d673f2cf0bb%3A0xfe377310d9a78fac!2zUGjDsm5nIGtow6FtIGNodXnDqm4ga2hvYSBwaOG7pSBz4bqjbiDEkOG6oWkgQW5oIHPhu5EgMQ!5e0!3m2!1svi!2s!4v1742546282056!5m2!1svi!2s" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
   ```

## Yêu cầu kỹ thuật bổ sung
1. **Quản lý bệnh nhân và dịch vụ y tế**
   - Chức năng chọn từng bệnh nhân trong danh sách đăng ký khám
   - Nhập phiếu khám bệnh, kê dịch vụ siêu âm, xét nghiệm, và kê đơn thuốc
   - Bảng cập nhật tên dịch vụ siêu âm xét nghiệm, giá dịch vụ
   - Đơn thuốc mẫu theo từng nhóm bệnh lý

2. **Mẫu phiếu siêu âm và xét nghiệm**
   - Mẫu phiếu siêu âm theo nhóm: sản khoa, phụ khoa, tổng quát
   - Mẫu phiếu siêu âm để chọn nhập kết quả
   - Khả năng tự cập nhật danh mục mẫu phiếu siêu âm và mẫu phiếu xét nghiệm

3. **Kết nối máy siêu âm**
   - Kết nối danh sách bệnh nhân đăng ký khám theo ngày hiện tại vào worklist trên máy siêu âm Voluson E10
