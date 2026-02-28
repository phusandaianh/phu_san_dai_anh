"""
Security enhancements for Phòng khám Đại Anh system
Triển khai các tính năng bảo mật cơ bản
"""

from flask import Flask, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
import os
from cryptography.fernet import Fernet
import bcrypt

# Cấu hình logging bảo mật
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('security.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
security_logger.addHandler(handler)

class SecurityManager:
    """Quản lý bảo mật hệ thống"""
    
    def __init__(self, app):
        self.app = app
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 phút
        
    def log_security_event(self, event_type, user_id=None, ip_address=None, details=None):
        """Ghi log sự kiện bảo mật"""
        security_logger.info(f"{event_type} - User: {user_id} - IP: {ip_address} - Details: {details}")
    
    def check_rate_limit(self, ip_address, max_requests=100, window=3600):
        """Kiểm tra rate limiting"""
        # Implement rate limiting logic
        # Có thể sử dụng Redis hoặc in-memory cache
        pass
    
    def validate_input(self, data, rules):
        """Validate input data theo rules"""
        errors = []
        
        for field, rule in rules.items():
            value = data.get(field, '')
            
            if rule.get('required') and not value:
                errors.append(f"{field} là bắt buộc")
                continue
                
            if value and rule.get('type') == 'email':
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                    errors.append(f"{field} không hợp lệ")
                    
            if value and rule.get('type') == 'phone':
                if not re.match(r'^\d{10,11}$', value):
                    errors.append(f"{field} phải có 10-11 số")
                    
            if value and rule.get('max_length'):
                if len(value) > rule['max_length']:
                    errors.append(f"{field} không được quá {rule['max_length']} ký tự")
                    
            if value and rule.get('pattern'):
                if not re.match(rule['pattern'], value):
                    errors.append(f"{field} không đúng định dạng")
        
        return errors
    
    def sanitize_input(self, data):
        """Làm sạch input để tránh XSS"""
        if isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        elif isinstance(data, str):
            # Loại bỏ các ký tự nguy hiểm
            dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', 'script', 'javascript']
            for char in dangerous_chars:
                data = data.replace(char, '')
            return data.strip()
        return data

class UserManager:
    """Quản lý người dùng và phân quyền"""
    
    def __init__(self, db):
        self.db = db
    
    def create_user(self, username, password, role='user', email=None):
        """Tạo user mới"""
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            email=email,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.db.session.add(user)
        self.db.session.commit()
        return user
    
    def authenticate_user(self, username, password):
        """Xác thực user"""
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash):
            # Cập nhật last_login
            user.last_login = datetime.utcnow()
            self.db.session.commit()
            return user
        
        return None
    
    def get_user_permissions(self, user_id):
        """Lấy quyền của user"""
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Định nghĩa permissions theo role
        permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users', 'view_reports'],
            'doctor': ['read', 'write', 'view_patients', 'manage_appointments'],
            'staff': ['read', 'write', 'manage_appointments'],
            'user': ['read']
        }
        
        return permissions.get(user.role, [])

class DataEncryption:
    """Mã hóa dữ liệu nhạy cảm"""
    
    def __init__(self):
        # Tạo hoặc load encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Lấy hoặc tạo encryption key"""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_data(self, data):
        """Mã hóa dữ liệu"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data):
        """Giải mã dữ liệu"""
        decrypted = self.cipher.decrypt(encrypted_data)
        return decrypted.decode('utf-8')

# Database Models cho bảo mật
class User(db.Model):
    """Bảng người dùng"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.String(20), default='user')  # admin, doctor, staff, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

class SecurityLog(db.Model):
    """Log bảo mật"""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(45))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    """Audit trail"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Decorators bảo mật
def require_auth(f):
    """Decorator yêu cầu xác thực"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token không được cung cấp'}), 401
        
        try:
            # Verify JWT token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'error': 'Token không hợp lệ'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated_function

def require_permission(permission):
    """Decorator yêu cầu quyền cụ thể"""
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            user_manager = UserManager(db)
            permissions = user_manager.get_user_permissions(current_user.id)
            
            if permission not in permissions:
                return jsonify({'error': 'Không có quyền thực hiện hành động này'}), 403
            
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(max_requests=100, window=3600):
    """Decorator rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            # Implement rate limiting logic here
            # Có thể sử dụng Redis hoặc in-memory cache
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Security middleware
def security_headers(response):
    """Thêm security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

# Input validation rules
VALIDATION_RULES = {
    'name': {'required': True, 'max_length': 100, 'pattern': r'^[a-zA-ZÀ-ỹ\s]+$'},
    'phone': {'required': True, 'type': 'phone', 'max_length': 11},
    'email': {'type': 'email', 'max_length': 120},
    'address': {'max_length': 200},
    'service_type': {'required': True, 'max_length': 100},
    'date_of_birth': {'required': True, 'pattern': r'^\d{4}-\d{2}-\d{2}$'}
}

# Security configuration
SECURITY_CONFIG = {
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this'),
    'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
    'BCRYPT_ROUNDS': 12,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 phút
    'SESSION_TIMEOUT': 3600,  # 1 giờ
    'PASSWORD_MIN_LENGTH': 8,
    'REQUIRE_HTTPS': True
}

def init_security(app, db):
    """Khởi tạo các tính năng bảo mật"""
    
    # Cấu hình JWT
    app.config['JWT_SECRET_KEY'] = SECURITY_CONFIG['JWT_SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = SECURITY_CONFIG['JWT_ACCESS_TOKEN_EXPIRES']
    
    jwt = JWTManager(app)
    
    # Thêm security headers
    app.after_request(security_headers)
    
    # Khởi tạo security manager
    security_manager = SecurityManager(app)
    
    return security_manager, jwt
