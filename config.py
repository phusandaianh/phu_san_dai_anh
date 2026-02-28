# -*- coding: utf-8 -*-
"""
Cấu hình ứng dụng - Phòng khám Đại Anh
Tách riêng để dễ thay đổi môi trường (dev/staging/prod)
"""
import os
from pathlib import Path

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Cấu hình chung"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'phong-kham-dai-anh-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR / "clinic.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    
    # Twilio (SMS)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID') or 'YOUR_TWILIO_ACCOUNT_SID'
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or 'YOUR_TWILIO_AUTH_TOKEN'
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') or 'YOUR_TWILIO_PHONE_NUMBER'
    
    # API
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'


class DevelopmentConfig(Config):
    """Cấu hình môi trường phát triển"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Cấu hình môi trường triển khai (LAN nội bộ)"""
    DEBUG = False
    ENV = 'production'


# Mapping môi trường
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
