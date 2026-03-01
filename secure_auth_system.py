"""
Hệ thống xác thực bảo mật cho Phòng khám Đại Anh
Triển khai authentication, authorization và security features
"""

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

# Import db from app
try:
    from app import db
except ImportError:
    # Fallback if not in app context
    db = SQLAlchemy()
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import bcrypt
import re
import secrets
import logging
from datetime import datetime, timedelta
import os
import json
from cryptography.fernet import Fernet

# Cấu hình logging bảo mật
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('security.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
security_logger.addHandler(handler)

class SecureAuthSystem:
    """Hệ thống xác thực bảo mật"""
    
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.failed_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 phút
        
    def log_security_event(self, event_type, user_id=None, ip_address=None, details=None):
        """Ghi log sự kiện bảo mật"""
        security_logger.info(f"{event_type} - User: {user_id} - IP: {ip_address} - Details: {details}")
    
    def validate_password_strength(self, password):
        """Kiểm tra độ mạnh mật khẩu"""
        if len(password) < 8:
            return False, "Mật khẩu phải có ít nhất 8 ký tự"
        
        if not re.search(r'[A-Z]', password):
            return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
        
        if not re.search(r'[a-z]', password):
            return False, "Mật khẩu phải có ít nhất 1 chữ thường"
        
        if not re.search(r'\d', password):
            return False, "Mật khẩu phải có ít nhất 1 số"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Mật khẩu phải có ít nhất 1 ký tự đặc biệt"
        
        return True, "Mật khẩu hợp lệ"
    
    def hash_password(self, password):
        """Hash mật khẩu với bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def verify_password(self, password, hashed):
        """Xác minh mật khẩu"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def check_account_lockout(self, username, ip_address):
        """Kiểm tra tài khoản có bị khóa không"""
        now = datetime.utcnow()
        key = f"{username}_{ip_address}"
        
        if key in self.failed_attempts:
            attempts, lockout_time = self.failed_attempts[key]
            
            if lockout_time and now < lockout_time:
                return True, f"Tài khoản bị khóa đến {lockout_time}"
            
            # Reset sau khi hết thời gian khóa
            if lockout_time and now >= lockout_time:
                del self.failed_attempts[key]
        
        return False, None
    
    def record_failed_attempt(self, username, ip_address):
        """Ghi nhận lần đăng nhập thất bại"""
        key = f"{username}_{ip_address}"
        now = datetime.utcnow()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = [1, None]
        else:
            attempts, _ = self.failed_attempts[key]
            attempts += 1
            
            if attempts >= self.max_attempts:
                lockout_time = now + timedelta(seconds=self.lockout_duration)
                self.failed_attempts[key] = [attempts, lockout_time]
                self.log_security_event('ACCOUNT_LOCKED', username, ip_address, f'Failed attempts: {attempts}')
            else:
                self.failed_attempts[key] = [attempts, None]
    
    def clear_failed_attempts(self, username, ip_address):
        """Xóa lịch sử đăng nhập thất bại"""
        key = f"{username}_{ip_address}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def validate_input(self, data, rules):
        """Validate input data"""
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

# Database Models
class User(db.Model):
    """Bảng người dùng"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # admin, doctor, staff, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    must_change_password = db.Column(db.Boolean, default=False)

class SecurityLog(db.Model):
    """Log bảo mật"""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
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

class Session(db.Model):
    """Quản lý session"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

# Decorators bảo mật
def require_auth(f):
    """Decorator yêu cầu xác thực"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = db.session.get(User, current_user_id)
        
        if not current_user or not current_user.is_active:
            return jsonify({'error': 'Tài khoản không hợp lệ'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated_function

def require_permission(permission):
    """Decorator yêu cầu quyền cụ thể"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(current_user, *args, **kwargs):
            user_permissions = get_user_permissions(current_user.role)
            
            if permission not in user_permissions:
                return jsonify({'error': 'Không có quyền thực hiện hành động này'}), 403
            
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator

def require_role(required_role):
    """Decorator yêu cầu role cụ thể"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role != required_role and current_user.role != 'admin':
                return jsonify({'error': 'Không có quyền truy cập'}), 403
            
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

def log_audit(action, table_name=None, record_id=None):
    """Decorator ghi audit log"""
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            # Ghi log trước khi thực hiện
            old_values = None
            if table_name and record_id:
                # Lấy giá trị cũ nếu có
                pass
            
            result = f(current_user, *args, **kwargs)
            
            # Ghi audit log
            audit_log = AuditLog(
                user_id=current_user.id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                ip_address=request.remote_addr,
                timestamp=datetime.utcnow()
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return result
        return decorated_function
    return decorator

# Helper functions
def get_user_permissions(role):
    """Lấy quyền theo role"""
    permissions = {
        'admin': [
            'read', 'write', 'delete', 'manage_users', 'view_reports',
            'manage_appointments', 'manage_patients', 'system_config'
        ],
        'doctor': [
            'read', 'write', 'view_patients', 'manage_appointments',
            'view_reports', 'manage_diagnosis'
        ],
        'staff': [
            'read', 'write', 'manage_appointments', 'view_patients'
        ],
        'user': ['read']
    }
    
    return permissions.get(role, [])

def create_session_token():
    """Tạo session token ngẫu nhiên"""
    return secrets.token_urlsafe(32)

def validate_session_token(token):
    """Validate session token"""
    session = Session.query.filter_by(
        session_token=token,
        is_active=True
    ).first()
    
    if not session or session.expires_at < datetime.utcnow():
        return None
    
    return session

# Security configuration
SECURITY_CONFIG = {
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production'),
    'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=1),
    'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=30),
    'BCRYPT_ROUNDS': 12,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,  # 5 phút
    'SESSION_TIMEOUT': 3600,  # 1 giờ
    'PASSWORD_MIN_LENGTH': 8,
    'REQUIRE_HTTPS': True,
    'PASSWORD_EXPIRY_DAYS': 90
}

# Input validation rules
VALIDATION_RULES = {
    'username': {
        'required': True, 
        'max_length': 80, 
        'pattern': r'^[a-zA-Z0-9_]+$'
    },
    'password': {
        'required': True, 
        'min_length': 8,
        'pattern': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    },
    'email': {
        'type': 'email', 
        'max_length': 120
    },
    'full_name': {
        'required': True, 
        'max_length': 100, 
        'pattern': r'^[a-zA-ZÀ-ỹ\s]+$'
    },
    'phone': {
        'type': 'phone', 
        'max_length': 11
    }
}

def init_secure_auth(app, db):
    """Khởi tạo hệ thống xác thực bảo mật"""
    
    # Cấu hình JWT
    app.config['JWT_SECRET_KEY'] = SECURITY_CONFIG['JWT_SECRET_KEY']
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = SECURITY_CONFIG['JWT_ACCESS_TOKEN_EXPIRES']
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = SECURITY_CONFIG['JWT_REFRESH_TOKEN_EXPIRES']
    
    jwt = JWTManager(app)
    
    # Khởi tạo auth system
    auth_system = SecureAuthSystem(app, db)
    
    return auth_system, jwt
