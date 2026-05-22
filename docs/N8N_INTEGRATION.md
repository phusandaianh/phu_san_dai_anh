# Tích hợp N8N — Ra lệnh cho Phòng khám Đại Anh

N8N (hoặc Zapier, script) gọi API lệnh có bảo mật API key để tự động hóa: danh sách khám hôm nay, thêm chỉ định siêu âm, v.v.

## Cấu hình server

Trên máy chạy app (Windows / LAN), đặt biến môi trường:

```text
N8N_API_KEY=dat-mot-chuoi-bao-mat-dai-ngau-nhien
```

Khởi động lại app Flask / Waitress sau khi đặt biến.

## Xác thực

Mỗi request cần một trong:

- Header: `X-N8N-API-Key: <N8N_API_KEY>`
- Header: `Authorization: Bearer <N8N_API_KEY>`

## Endpoints

| Method | URL | Mô tả |
|--------|-----|--------|
| GET | `/api/n8n/commands` | Danh sách lệnh + hướng dẫn params |
| POST | `/api/n8n/command` | Thực thi một lệnh |

Base URL ví dụ LAN: `http://10.17.2.2:5000`

## Lệnh hỗ trợ

### 1. `list_today_appointments`

Danh sách lịch khám **hôm nay**.

```json
{
  "command": "list_today_appointments",
  "params": {
    "q": "Hà Ngọc",
    "phone": "0912345678",
    "status": ""
  }
}
```

### 2. `list_clinical_services`

Liệt kê dịch vụ CLS (để biết `service_id` / tên chính xác trong DB).

```json
{
  "command": "list_clinical_services",
  "params": {
    "q": "siêu âm",
    "ultrasound_only": true
  }
}
```

### 3. `add_clinical_service`

Thêm dịch vụ cho lịch khám (ưu tiên **hôm nay**).

```json
{
  "command": "add_clinical_service",
  "params": {
    "patient_name": "Hà Ngọc",
    "phone": "0912345678",
    "service_name": "Siêu âm thai 12 tuần",
    "doctor_name": "PK Đại Anh"
  }
}
```

Hoặc chỉ định rõ:

```json
{
  "command": "add_clinical_service",
  "params": {
    "appointment_id": 15,
    "service_id": 3
  }
}
```

### 4. `add_ultrasound_12w`

Alias: tự tìm dịch vụ siêu âm thai ~12 tuần trong DB rồi thêm (cùng params như trên).

```json
{
  "command": "add_ultrasound_12w",
  "params": {
    "patient_name": "Hà Ngọc",
    "phone": "0912345678"
  }
}
```

## Gợi ý workflow N8N

### A. Webhook + lệnh có cấu trúc

1. **Webhook** (POST) nhận body từ chat/voice bot.
2. **HTTP Request** → `POST http://10.17.2.2:5000/api/n8n/command`
   - Header: `X-N8N-API-Key`
   - Body JSON: `command` + `params`
3. **Respond to Webhook** — trả `message` trong response cho người dùng.

### B. Lịch tự động sáng (danh sách khám)

1. **Schedule Trigger** — 7:00 mỗi ngày.
2. **HTTP Request** — `list_today_appointments`.
3. **Slack / Zalo / Email** — format `data.appointments`.

### C. Thêm siêu âm từ chat (có AI)

1. Webhook nhận: *"Thêm siêu âm thai 12 tuần cho Hà Ngọc sđt 0912..."*
2. Node **OpenAI / Agent** parse JSON:

```json
{
  "command": "add_ultrasound_12w",
  "params": {
    "patient_name": "...",
    "phone": "..."
  }
}
```

3. HTTP Request gọi `/api/n8n/command`.

Hoặc gửi trực tiếp (không AI) với field `text`:

```json
{
  "text": "danh sách khám hôm nay"
}
```

```json
{
  "text": "thêm siêu âm thai 12 tuần",
  "patient_name": "Hà Ngọc",
  "phone": "0912345678"
}
```

## Response mẫu

Thành công:

```json
{
  "success": true,
  "command": "add_ultrasound_12w",
  "message": "Đã thêm \"Siêu âm thai 12w\" cho Hà Ngọc (lịch #15). Đã kích hoạt đồng bộ worklist siêu âm.",
  "data": {
    "appointment_id": 15,
    "service_name": "...",
    "is_ultrasound": true
  }
}
```

Lỗi (nhiều lịch trùng):

```json
{
  "success": false,
  "code": "ambiguous",
  "error": "Nhiều lịch khám trùng điều kiện hôm nay — cần appointment_id cụ thể.",
  "details": [ { "appointment_id": 1, ... }, { "appointment_id": 2, ... } ]
}
```

## Lưu ý

- Cần **mwl_server.py** chạy nếu thêm dịch vụ siêu âm (tự đồng bộ worklist).
- Tên dịch vụ phải khớp DB — dùng `list_clinical_services` nếu `add_*` báo không tìm thấy.
- Không commit `N8N_API_KEY` lên git; chỉ đặt trên máy server.
