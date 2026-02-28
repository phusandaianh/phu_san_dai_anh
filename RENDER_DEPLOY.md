# Hướng dẫn Deploy lên Render

## Đã chuẩn bị

- **render.yaml** – Cấu hình Blueprint cho Render
- **gunicorn** – Đã thêm vào requirements.txt
- **build.sh** – Tạo thư mục uploads
- **runtime.txt** – Python 3.11

## Các bước deploy

### 1. Đẩy code lên GitHub

```bash
git add .
git commit -m "Chuẩn bị deploy Render"
git push origin main
```

### 2. Tạo Web Service trên Render

1. Vào [dashboard.render.com](https://dashboard.render.com)
2. **New** → **Web Service**
3. Kết nối repo GitHub: `phusandaianh/phu_san_dai_anh`
4. Cấu hình:
   - **Name:** `phong-kham-dai-anh`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -b 0.0.0.0:$PORT wsgi:app`
   - **Instance Type:** Free (hoặc trả phí nếu cần)

### 3. Hoặc dùng Blueprint (render.yaml)

1. **New** → **Blueprint**
2. Kết nối repo và chọn `render.yaml`
3. Render sẽ tạo service theo cấu hình trong file

## Lưu ý

- **SQLite:** Dữ liệu sẽ mất khi service restart/redeploy. Nếu cần lưu trữ lâu dài, nên dùng PostgreSQL (Render có sẵn).
- **Uploads:** Thư mục `uploads/` không được commit (đã thêm vào .gitignore). File upload trên Render sẽ mất khi redeploy.
- **Free tier:** Service sẽ sleep sau ~15 phút không có truy cập, lần truy cập đầu tiên có thể chậm.

## URL sau khi deploy

Render sẽ cấp URL dạng: `https://phong-kham-dai-anh.onrender.com`
