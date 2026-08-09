# Đặt lịch online (Render) ↔ Phòng khám local (pk)

## Mô hình

| Vai trò | Domain | Máy | `SYNC_ROLE` |
|--------|--------|-----|-------------|
| Đặt lịch bệnh nhân (luôn online) | https://booking.phusandaianh.io.vn | Render | `online` |
| Phòng khám vận hành | https://pk.phusandaianh.io.vn | Máy chủ phòng khám | `local` |

```text
Bệnh nhân → booking.phusandaianh.io.vn (Render)
                 │
                 │  lịch hẹn lưu trên cloud + SyncEvent
                 ▼
Máy chủ tắt: pk tắt, bệnh nhân vẫn đặt được trên booking.*
Máy chủ bật: local kéo lịch hẹn về pk + đẩy lịch làm việc lên cloud
```

- **Máy chủ tắt:** `pk.*` tắt; bệnh nhân đăng ký tại `booking.*`.
- **Máy chủ bật:** vòng sync local (mỗi ~15s) kéo hẹn từ Render về `pk`, đẩy lịch/hẹn nội bộ lên Render.
- Khi local khởi động: tự đẩy lịch làm việc ~30 ngày tới lên Render để có slot đặt.

Cùng một codebase (`booking.html` + `app.py`). Phân biệt bằng biến môi trường.

---

## 1) Deploy Render (`booking.phusandaianh.io.vn`)

1. Đẩy code lên GitHub, tạo **Web Service** (hoặc Blueprint từ `render.yaml`).
2. **Start command:** `gunicorn -b 0.0.0.0:$PORT wsgi:app`
3. Environment (xem thêm `render.env.example`):

```env
SYNC_ROLE=online
SYNC_TOKEN=PKDA_SYNC_2026
PUBLIC_BOOKING_URL=https://booking.phusandaianh.io.vn
BOOKING_HOST_PREFIXES=booking.,dangki.
```

4. Custom Domain: `booking.phusandaianh.io.vn` → service Render (DNS CNAME theo hướng dẫn Render).
5. **PostgreSQL (khuyến nghị mạnh):** gắn DB trên Render, set `DATABASE_URL`. SQLite trên free tier sẽ mất dữ liệu khi redeploy — nguy hiểm nếu bệnh nhân đặt lúc máy chủ tắt.
6. Giữ service không ngủ (free tier): UptimeRobot / cron ping `https://booking.phusandaianh.io.vn/api/health` mỗi 5–10 phút.

Kiểm tra: mở https://booking.phusandaianh.io.vn → phải ra trang đặt lịch (`booking.html`).

---

## 2) Cấu hình máy chủ phòng khám (`pk.*`)

File `sync_local.env` (đã có sẵn, service systemd cũng nạp file này):

```env
SYNC_ROLE=local
SYNC_REMOTE_URL=https://booking.phusandaianh.io.vn
SYNC_TOKEN=PKDA_SYNC_2026
SYNC_PEER_APPOINTMENTS_URL=https://booking.phusandaianh.io.vn
SYNC_PEER_TOKEN=PKDA_SYNC_2026
SYNC_INTERVAL_SECONDS=15
```

`SYNC_TOKEN` phải **giống hệt** bên Render.

Chạy app bằng systemd `phong-kham-dai-anh` hoặc:

```bash
cd /mnt/Data/Du_Lieu_Phong_Kham/Phong_kham_dai_anh
source .venv/bin/activate
python run_waitress.py
```

Log phải có dòng tương tự:

```text
[SYNC] local loop started. remote=https://booking.phusandaianh.io.vn
[SYNC] boot schedule push: mirrored=...
```

Trong Admin → xem trạng thái sync (`/api/sync/status`).

DNS `pk.phusandaianh.io.vn` trỏ về IP máy chủ phòng khám (reverse proxy HTTPS nếu cần).

---

## 3) Đồng bộ dữ liệu gì?

| Dữ liệu | Chiều |
|---------|--------|
| Lịch làm việc (ca khám / bác sĩ) | Local → Render (boot + mỗi lần sửa lịch) |
| Bệnh nhân đặt trên booking.* | Render → Local (khi máy chủ bật, pull) |
| Đặt lịch nội bộ trên pk | Local → Render (push / mirror) |
| Đổi giờ / hủy hẹn | Hai chiều qua SyncEvent |

---

## 4) Checklist vận hành hàng ngày

1. Trên **pk**: lên lịch làm việc trước khi tắt máy (hoặc để boot push chạy khi bật lại).
2. Bệnh nhân dùng link: **https://booking.phusandaianh.io.vn**
3. Tiếp tân nội bộ: `https://pk.phusandaianh.io.vn/booking.html?internal=1` (hoặc LAN `:5000`)
4. Sau khi bật máy chủ: vài phút sau, hẹn online xuất hiện trong **Danh sách khám** trên pk.
5. Nếu slot trên booking trống: vào Admin pk → đồng bộ lịch làm việc (`POST /api/work-schedule/sync` hoặc nút sync trên admin).

---

## 5) Link dùng thực tế

- Bệnh nhân online: https://booking.phusandaianh.io.vn  
- Phòng khám (khi máy chủ bật): https://pk.phusandaianh.io.vn  
- Health cloud: https://booking.phusandaianh.io.vn/api/health  

> Lưu ý chính tả domain: `phusandaianh` (không phải `phusandaiainh`).
