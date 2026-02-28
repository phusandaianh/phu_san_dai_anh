# Kiến trúc REST API - Phòng khám Đại Anh

## Tổng quan

Ứng dụng đã được chuyển sang kiến trúc Flask REST API với Blueprint, dễ mở rộng và nâng cấp.

## Cấu trúc thư mục

```
Phong_kham_dai_anh_maytinh/
├── app.py              # Entry point chính, models, routes còn lại
├── run.py              # Khởi chạy (python run.py)
├── wsgi.py             # WSGI cho Gunicorn/Waitress
├── config.py           # Cấu hình (dev/prod)
├── extensions.py       # Flask extensions (db, ...)
├── api/                # REST API package
│   ├── __init__.py     # register_blueprints
│   └── v1/             # API version 1
│       ├── __init__.py # Tổng hợp blueprints
│       ├── auth.py     # /api/login
│       ├── patients.py # /api/patients/...
│       └── appointments.py  # /api/appointments/...
├── clinic.db           # Database
└── ...
```

## API Endpoints (đã chuyển sang API module)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | /api/login | Đăng nhập |
| GET | /api/patients/<id> | Chi tiết bệnh nhân |
| PUT | /api/patients/<id> | Cập nhật bệnh nhân |
| GET | /api/patients/by-phone?phone=xxx | Tìm theo SĐT |
| GET | /api/appointments/today | Lịch hôm nay |
| GET | /api/appointments/by-date?date=yyyy-mm-dd | Lịch theo ngày |
| GET | /api/appointments/<id> | Chi tiết lịch hẹn |
| GET/PUT | /api/appointments/<id>/diagnosis | Chẩn đoán |
| GET/PUT | /api/appointments/<id>/notes | Ghi chú |

## Cách thêm API mới

1. Tạo file mới trong `api/v1/`, ví dụ `api/v1/lab.py`:

```python
from flask import Blueprint, request, jsonify

lab_bp = Blueprint('lab', __name__)

@lab_bp.route('/lab-orders', methods=['GET'])
def list_orders():
    from app import LabOrder
    orders = LabOrder.query.all()
    return jsonify([...])
```

2. Đăng ký trong `api/v1/__init__.py`:

```python
from api.v1 import auth, patients, appointments, lab
api_v1_bp.register_blueprint(lab.lab_bp, url_prefix='')
```

3. Chuyển route tương ứng từ `app.py` sang module mới.

## Deploy LAN nội bộ

```bash
# Development
python run.py

# Production (chạy ổn định hơn)
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
```

Hoặc dùng **KHỞI ĐỘNG PHÒNG KHÁM.bat**.

## Lộ trình mở rộng

- [ ] Chuyển thêm routes: lab, clinical-services, users, ...
- [ ] Thêm API versioning: /api/v2/ khi cần breaking changes
- [ ] Tách models ra `models/` package
- [ ] Thêm API documentation (Swagger/OpenAPI)
- [ ] Thêm rate limiting, caching cho production
