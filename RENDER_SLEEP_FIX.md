# Khắc phục Render vẫn bị ngủ (Sleep)

Render Free tier **tự động sleep** sau **15 phút** không có truy cập. Nếu service vẫn ngủ, kiểm tra các bước sau:

---

## 1. Xác nhận URL chính xác

1. Vào [dashboard.render.com](https://dashboard.render.com)
2. Chọn service **phong-kham-dai-anh**
3. Copy **URL** từ mục "Your service is live at" (ví dụ: `https://phong-kham-dai-anh.onrender.com`)
4. **Lưu ý:** URL có thể khác nếu bạn đổi tên service hoặc dùng subdomain tùy chỉnh

---

## 2. Kiểm tra endpoint hoạt động

Mở trình duyệt hoặc dùng curl:

```
https://<URL-CỦA-BẠN>/api/health
https://<URL-CỦA-BẠN>/ping
https://<URL-CỦA-BẠN>/healthz
```

**Response đúng:** `{"status": "ok", "timestamp": "..."}` với HTTP 200

Nếu lỗi 404/500 → kiểm tra deploy và code.

---

## 3. Cấu hình Cron / UptimeRobot

### Cách A: UptimeRobot (Khuyến nghị – 5 phút/lần)

1. Đăng ký miễn phí: [uptimerobot.com](https://uptimerobot.com)
2. **Add New Monitor**
3. Cấu hình:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Keep Render awake
   - **URL:** `https://phong-kham-dai-anh.onrender.com/api/health`
   - **Monitoring Interval:** 5 phút (tối đa cho free tier)
4. **Create Monitor**

### Cách B: cron-job.org (10 phút/lần)

1. Đăng ký: [cron-job.org](https://cron-job.org)
2. **Create cronjob**
3. Cấu hình:
   - **Title:** Keep Render awake
   - **URL:** `https://phong-kham-dai-anh.onrender.com/api/health`
   - **Schedule:** `*/10 * * * *` (mỗi 10 phút)
   - **Request Method:** GET
4. **Create** và bật **Enabled**

---

## 4. Kiểm tra Cron đã chạy

### UptimeRobot
- Vào **Dashboard** → xem cột **Status** (Up/Down)
- Vào **Log** → xem lịch sử request

### cron-job.org
- Vào **Dashboard** → **Executions**
- Kiểm tra có request thành công (HTTP 200) không

---

## 5. Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|-------------|-------------|------------|
| Lần đầu truy cập chậm 30–60s | Cold start sau khi sleep | Bình thường. Cron/UptimeRobot sẽ giữ service không ngủ. |
| Service vẫn sleep dù đã cấu hình cron | URL sai hoặc cron không chạy | Kiểm tra URL, xem log Executions. |
| 404 trên /api/health | Deploy lỗi hoặc route sai | Kiểm tra `app.py` có route `/api/health`. |
| 502/503 | App crash khi khởi động | Xem **Logs** trên Render Dashboard. |

---

## 6. Tần suất gợi ý

- **Render sleep sau:** ~15 phút
- **Nên ping:** mỗi **5–10 phút**
- **UptimeRobot free:** tối đa 5 phút
- **cron-job.org free:** thường 10–14 phút

---

## 7. Lệnh test nhanh

```bash
# Thay URL bằng URL thực tế của bạn
curl -I https://phong-kham-dai-anh.onrender.com/api/health
```

Nếu thấy `HTTP/2 200` → endpoint hoạt động, chỉ cần cấu hình ping đúng.
