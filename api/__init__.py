# -*- coding: utf-8 -*-
"""
Flask REST API - Phòng khám Đại Anh
Cấu trúc module để dễ mở rộng, nâng cấp
"""
from flask import Blueprint

def register_blueprints(app):
    """Đăng ký tất cả API blueprints"""
    from api.v1 import api_v1_bp
    # Prefix /api - giữ tương thích với frontend hiện tại
    app.register_blueprint(api_v1_bp, url_prefix='/api')
