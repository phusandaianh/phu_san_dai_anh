# -*- coding: utf-8 -*-
"""Tạo bảng quick_links nếu chưa có. Chạy: python create_quick_links_table.py"""
import sys
sys.path.insert(0, '.')
from app import app, db
with app.app_context():
    db.create_all()
    print('Đã tạo bảng quick_links (nếu chưa có). Khởi động lại server và thử lại.')
