# -*- coding: utf-8 -*-
"""
Flask extensions - khởi tạo db và các extension khác
Tách riêng để tránh circular import khi dùng trong api/
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
