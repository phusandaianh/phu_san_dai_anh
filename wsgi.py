# -*- coding: utf-8 -*-
"""
WSGI entry point - dùng với Gunicorn/Waitress khi deploy production
Ví dụ: waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
"""
from app import app

# Gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
# Waitress: waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
