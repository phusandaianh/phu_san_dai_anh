# Hướng dẫn triển khai mạng nội bộ - Phòng khám Đại Anh

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                    MÁY CHỦ PHÒNG KHÁM                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  • Web Server (Flask - port 5000)                            │ │
│  │  • Database SQLite (clinic.db) - Dữ liệu bệnh nhân           │ │
│  │  • DICOM MWL Server (port 104) - Đồng bộ Voluson E10         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  IP: 192.168.x.x (ví dụ: 192.168.1.100)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                    Mạng LAN nội bộ
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Máy 1        │    │  Máy 2        │    │  Máy khác     │
│  Truy cập     │    │  Truy cập     │    │  (tùy chọn)   │
│  qua trình    │    │  qua trình    │    │               │
│  duyệt web    │    │  duyệt web    │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

**Dữ liệu bệnh nhân** được lưu tập trung tại máy chủ (`clinic.db`). Tất cả máy truy cập đều làm việc với cùng một nguồn dữ liệu.

---

## Bước 1: Chuẩn bị máy chủ

### 1.1. Cài đặt Python và thư viện

- Python 3.10 trở lên
- Chạy: `pip install -r requirements.txt`

### 1.2. Lấy địa chỉ IP máy chủ

Mở Command Prompt hoặc PowerShell trên máy chủ, chạy:

```cmd
ipconfig
```

Tìm dòng **IPv4 Address** (ví dụ: `192.168.1.100`). Đây là địa chỉ các máy khác sẽ dùng để truy cập.

---

## Bước 2: Khởi động máy chủ

### Cách 1: Dùng file batch (khuyến nghị)

1. Double-click **KHỞI ĐỘNG PHÒNG KHÁM.bat**
2. Sẽ mở 2 cửa sổ:
   - **Web Server** (port 5000)
   - **DICOM MWL Server** (port 104)

### Cách 2: Chạy thủ công

**Terminal 1 – Web Server:**
```cmd
cd D:\phusandaianh\DU_AN_AI\Phong_kham_dai_anh_maytinh
python app.py
```

**Terminal 2 – DICOM MWL Server** (nếu dùng Voluson E10):
```cmd
cd D:\phusandaianh\DU_AN_AI\Phong_kham_dai_anh_maytinh
python dicom_mwl_server.py
```

---

## Bước 3: Truy cập từ máy khác (1–2 máy)

Trên máy 1 và máy 2, mở trình duyệt (Chrome, Edge, Firefox) và truy cập:

```
https://[IP_MÁY_CHỦ]:5000
```

Ví dụ: `https://10.8.126.73:5000`

**Lần đầu truy cập:** Trình duyệt có thể hiển thị cảnh báo chứng chỉ (vì dùng chứng chỉ tự ký). Chọn **"Continue to site"** hoặc **"Chuyển tiếp đến trang web"** để tiếp tục.

- Đăng nhập bằng tài khoản admin hoặc nhân viên
- Dữ liệu bệnh nhân được đồng bộ theo thời gian thực vì tất cả đều dùng chung database trên máy chủ

---

## Bước 4: Cấu hình Firewall (nếu không truy cập được)

Nếu máy khác không kết nối được, cần mở port trên máy chủ:

### Windows Firewall

1. Mở **Windows Defender Firewall** → **Advanced settings**
2. Chọn **Inbound Rules** → **New Rule**
3. Chọn **Port** → Next
4. Chọn **TCP**, nhập port: **5000** (và **104** nếu dùng DICOM)
5. Chọn **Allow the connection**
6. Áp dụng cho **Private** (mạng nội bộ)
7. Đặt tên: "Phong kham Dai Anh Web"

Hoặc chạy PowerShell **với quyền Administrator**:

```powershell
New-NetFirewallRule -DisplayName "Phong kham Dai Anh Web" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "Phong kham DICOM MWL" -Direction Inbound -Protocol TCP -LocalPort 104 -Action Allow -Profile Private
```

---

## Lưu ý quan trọng

| Nội dung | Mô tả |
|----------|-------|
| **Dữ liệu tập trung** | `clinic.db` nằm trên máy chủ. Cần sao lưu định kỳ thư mục dự án |
| **Mạng nội bộ** | Chỉ nên dùng trong mạng LAN phòng khám |
| **Đăng nhập** | Mỗi nhân viên có tài khoản riêng để phân quyền |
| **Đồng thời** | 1–2 máy truy cập cùng lúc hoạt động ổn định |

---

## Sao lưu dữ liệu

Định kỳ sao lưu file:

- `clinic.db` – database bệnh nhân
- `uploads/` – file đính kèm (PDF, ảnh…)
- `received_dicoms/` – ảnh DICOM từ Voluson

---

## Xử lý sự cố

| Vấn đề | Cách xử lý |
|--------|------------|
| Máy khác không truy cập được | Kiểm tra firewall, đảm bảo cùng mạng LAN |
| Lỗi khi đăng nhập | Kiểm tra tài khoản trong trang admin |
| DICOM không đồng bộ | Kiểm tra DICOM MWL Server đang chạy, cấu hình IP Voluson |
