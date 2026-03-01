# Giữ Render không ngủ

Render Free tier sẽ **sleep** sau ~15 phút không có truy cập. Dùng dịch vụ ping định kỳ để giữ service luôn sẵn sàng.

**Nếu vẫn bị ngủ:** Xem [RENDER_SLEEP_FIX.md](RENDER_SLEEP_FIX.md) để kiểm tra và khắc phục.

---

## Cách 1: UptimeRobot (Khuyến nghị – ping 5 phút)

1. Đăng ký miễn phí: [uptimerobot.com](https://uptimerobot.com)
2. Add New Monitor → HTTP(s)
3. URL: `https://phong-kham-dai-anh.onrender.com/api/health`
4. Interval: **5 phút**
5. Create Monitor

---

## Cách 2: cron-job.org (ping 10 phút)

### Bước 1: Đăng ký cron-job.org

1. Vào [cron-job.org](https://cron-job.org)
2. Đăng ký tài khoản miễn phí
3. Xác nhận email

## Bước 2: Tạo Cron Job

1. Đăng nhập → **Create cronjob**
2. Điền thông tin:

| Mục | Giá trị |
|-----|---------|
| **Title** | Keep Render awake |
| **URL** | `https://phong-kham-dai-anh.onrender.com/api/health` |
| **Schedule** | Mỗi 10 phút (hoặc 14 phút – trước khi sleep) |
| **Request Method** | GET |

3. **Advanced** (tùy chọn):
   - **Request timeout:** 30 giây
   - **Failure notifications:** Bật nếu muốn nhận email khi lỗi

4. **Create cronjob**

## Bước 3: Kiểm tra

- Cron job sẽ chạy theo lịch (ví dụ mỗi 10 phút)
- Vào **Dashboard** → **Executions** để xem lịch sử
- Nếu status 200 → Render được giữ không ngủ

## Lưu ý

- **URL:** Thay `phong-kham-dai-anh` bằng tên service thực tế trên Render
- **Tần suất:** Nên ≤ 14 phút để tránh Render sleep
- **Endpoint:** `/api/health` nhẹ, trả về JSON nhanh

## Endpoint health check

```
GET https://<your-app>.onrender.com/api/health
GET https://<your-app>.onrender.com/ping
GET https://<your-app>.onrender.com/healthz
```

Response: `{"status": "ok", "timestamp": "..."}`
