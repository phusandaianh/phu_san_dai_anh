# Chạy MWL Server (`mwl_server.py`) như Windows Service

Bạn có thể chạy MWL SCP server như một dịch vụ Windows để tự động khởi động cùng hệ thống và quản lý dễ dàng.

## Cách 1: Dùng NSSM (khuyên dùng)
### Bước 1: Tải và giải nén NSSM
- Tải NSSM tại: https://nssm.cc/download
- Giải nén, ví dụ: `C:\nssm\nssm.exe`

### Bước 2: Đăng ký dịch vụ
Mở PowerShell với quyền Administrator và chạy:

```powershell
C:\nssm\nssm.exe install MWLServer
```

- Trong cửa sổ hiện ra:
  - **Path**: chọn đường dẫn tới python.exe (ví dụ: `C:\Users\<user>\AppData\Local\Programs\Python\Python39\python.exe`)
  - **Arguments**: nhập `mwl_server.py`
  - **Startup directory**: chọn thư mục chứa file `mwl_server.py` (ví dụ: `j:\DU_AN_AI\Phong_kham_dai_anh`)
- Nhấn "Install service"

### Bước 3: Khởi động dịch vụ
```powershell
Start-Service MWLServer
```

### Bước 4: Kiểm tra trạng thái
```powershell
Get-Service MWLServer
```

### Gỡ dịch vụ (nếu cần)
```powershell
C:\nssm\nssm.exe remove MWLServer confirm
```

## Cách 2: Dùng lệnh sc create (không khuyến khích nếu script cần môi trường ảo)
```powershell
sc create MWLServer binPath= "C:\Users\<user>\AppData\Local\Programs\Python\Python39\python.exe j:\DU_AN_AI\Phong_kham_dai_anh\mwl_server.py" start= auto
```
- Để xóa dịch vụ: `sc delete MWLServer`

## Lưu ý
- Đảm bảo file `mwl_server.py` chạy OK bằng lệnh thủ công trước khi tạo service.
- Nếu dùng môi trường ảo (venv), nên dùng NSSM và chỉ định python.exe trong venv.
- Để xem log, nên sửa `mwl_server.py` ghi log ra file hoặc dùng NSSM để redirect output.

---
**Hỏi thêm:** Nếu cần script tự động hoặc muốn log chi tiết, hãy yêu cầu!
