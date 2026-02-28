# Hướng dẫn sử dụng tài khoản Admin - Phòng khám Đại Anh

## 🔐 Thông tin tài khoản Admin

- **Tên đăng nhập:** `daihn`
- **Mật khẩu:** `190514@Da`
- **Email:** `admin@phongkhamdaianh.com`
- **Vai trò:** Admin (Quản trị viên hệ thống)

## 🚀 Cách truy cập trang quản lý người dùng

1. Mở trình duyệt và truy cập: `http://127.0.0.1:5000/users.html`
2. Nhập thông tin đăng nhập:
   - Tên đăng nhập: `daihn`
   - Mật khẩu: `190514@Da`
3. Nhấn nút "Đăng nhập"

## ✨ Chức năng có sẵn

### Quản lý người dùng
- ✅ **Xem danh sách người dùng** - Hiển thị tất cả người dùng trong hệ thống
- ✅ **Thêm người dùng mới** - Tạo tài khoản mới với các vai trò khác nhau
- ✅ **Sửa thông tin người dùng** - Cập nhật thông tin, vai trò, trạng thái
- ✅ **Xóa người dùng** - Xóa tài khoản không cần thiết
- ✅ **Quản lý vai trò** - Phân quyền cho từng người dùng

### Các vai trò có sẵn
- **Admin** - Quản trị viên hệ thống (toàn quyền)
- **Doctor** - Bác sĩ
- **Nurse** - Y tá  
- **Receptionist** - Lễ tân

### Trạng thái tài khoản
- **Hoạt động** - Tài khoản có thể đăng nhập
- **Không hoạt động** - Tài khoản bị vô hiệu hóa

## 🔧 Cách tạo lại tài khoản admin (nếu cần)

Nếu cần tạo lại hoặc cập nhật tài khoản admin, chạy lệnh:

```bash
python create_admin_daihn.py
```

## 🛡️ Bảo mật

- Tài khoản admin được bảo vệ bằng mật khẩu mạnh
- Mật khẩu được mã hóa bằng bcrypt
- Phiên đăng nhập được lưu trong localStorage
- Có thể đăng xuất bất kỳ lúc nào

## 📝 Lưu ý quan trọng

1. **Bảo mật thông tin đăng nhập** - Không chia sẻ thông tin tài khoản admin
2. **Thay đổi mật khẩu định kỳ** - Nên thay đổi mật khẩu admin sau khi triển khai
3. **Sao lưu dữ liệu** - Thường xuyên sao lưu cơ sở dữ liệu
4. **Kiểm tra logs** - Theo dõi logs để phát hiện hoạt động bất thường

## 🆘 Xử lý sự cố

### Không thể đăng nhập
1. Kiểm tra tên đăng nhập và mật khẩu
2. Đảm bảo server đang chạy
3. Kiểm tra kết nối mạng
4. Xóa cache trình duyệt và thử lại

### Quên mật khẩu
1. Chạy script tạo lại admin: `python create_admin_daihn.py`
2. Hoặc truy cập trực tiếp database để reset

### Lỗi kết nối
1. Kiểm tra server có đang chạy không
2. Kiểm tra port 5000 có bị chặn không
3. Khởi động lại server nếu cần

---

**Phòng khám Phụ Sản Đại Anh**  
*Hệ thống quản lý thông tin y tế*
