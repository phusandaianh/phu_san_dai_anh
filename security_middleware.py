"""
Security middleware và utilities cho hệ thống Phòng khám Đại Anh
Triển khai các lớp bảo mật và monitoring
"""

from flask import Flask, request, jsonify, session, g
from functools import wraps
import time
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict, deque
import threading

# Cấu hình logging bảo mật
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)
handler = logging.FileHandler('security.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
security_logger.addHandler(handler)

class RateLimiter:
    """Rate limiting middleware"""
    
    def __init__(self, max_requests=100, window=3600):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier):
        """Kiểm tra xem request có được phép không"""
        now = time.time()
        
        with self.lock:
            # Làm sạch requests cũ
            while self.requests[identifier] and self.requests[identifier][0] <= now - self.window:
                self.requests[identifier].popleft()
            
            # Kiểm tra số lượng requests
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # Thêm request mới
            self.requests[identifier].append(now)
            return True
    
    def get_remaining_requests(self, identifier):
        """Lấy số requests còn lại"""
        now = time.time()
        
        with self.lock:
            # Làm sạch requests cũ
            while self.requests[identifier] and self.requests[identifier][0] <= now - self.window:
                self.requests[identifier].popleft()
            
            return max(0, self.max_requests - len(self.requests[identifier]))

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Thêm security headers"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response

class InputValidator:
    """Input validation và sanitization"""
    
    @staticmethod
    def sanitize_string(value):
        """Làm sạch string input"""
        if not isinstance(value, str):
            return value
        
        # Loại bỏ các ký tự nguy hiểm
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>'
        ]
        
        for pattern in dangerous_patterns:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        # Loại bỏ các ký tự đặc biệt nguy hiểm
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        import re
        pattern = r'^\d{10,11}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_date(date_string, format='%Y-%m-%d'):
        """Validate date format"""
        try:
            datetime.strptime(date_string, format)
            return True
        except ValueError:
            return False

class SecurityMonitor:
    """Security monitoring và alerting"""
    
    def __init__(self):
        self.suspicious_activities = []
        self.failed_logins = defaultdict(int)
        self.alert_thresholds = {
            'failed_logins': 5,
            'suspicious_requests': 10,
            'rate_limit_violations': 20
        }
    
    def log_suspicious_activity(self, activity_type, details, ip_address, user_id=None):
        """Ghi log hoạt động đáng ngờ"""
        activity = {
            'type': activity_type,
            'details': details,
            'ip_address': ip_address,
            'user_id': user_id,
            'timestamp': datetime.utcnow()
        }
        
        self.suspicious_activities.append(activity)
        security_logger.warning(f"SUSPICIOUS_ACTIVITY: {activity_type} - {details} - IP: {ip_address}")
        
        # Kiểm tra ngưỡng cảnh báo
        self.check_alert_thresholds(activity_type, ip_address)
    
    def check_alert_thresholds(self, activity_type, ip_address):
        """Kiểm tra ngưỡng cảnh báo"""
        if activity_type == 'failed_login':
            self.failed_logins[ip_address] += 1
            
            if self.failed_logins[ip_address] >= self.alert_thresholds['failed_logins']:
                self.send_security_alert('MULTIPLE_FAILED_LOGINS', {
                    'ip_address': ip_address,
                    'count': self.failed_logins[ip_address]
                })
    
    def send_security_alert(self, alert_type, details):
        """Gửi cảnh báo bảo mật"""
        alert = {
            'type': alert_type,
            'details': details,
            'timestamp': datetime.utcnow(),
            'severity': 'HIGH'
        }
        
        security_logger.critical(f"SECURITY_ALERT: {alert_type} - {details}")
        
        # Có thể gửi email, SMS, hoặc webhook
        # self.send_notification(alert)
    
    def reset_failed_logins(self, ip_address):
        """Reset số lần đăng nhập thất bại"""
        if ip_address in self.failed_logins:
            del self.failed_logins[ip_address]

class CSRFProtection:
    """CSRF protection"""
    
    @staticmethod
    def generate_csrf_token():
        """Tạo CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token, session_token):
        """Validate CSRF token"""
        if not token or not session_token:
            return False
        
        # So sánh token với session
        return token == session_token

class SecurityAudit:
    """Security audit và compliance"""
    
    def __init__(self):
        self.audit_logs = []
    
    def log_audit_event(self, user_id, action, resource, old_value=None, new_value=None):
        """Ghi audit log"""
        audit_event = {
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'old_value': old_value,
            'new_value': new_value,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'timestamp': datetime.utcnow()
        }
        
        self.audit_logs.append(audit_event)
        security_logger.info(f"AUDIT: {action} on {resource} by user {user_id}")
    
    def get_audit_trail(self, user_id=None, action=None, start_date=None, end_date=None):
        """Lấy audit trail"""
        filtered_logs = self.audit_logs
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log['user_id'] == user_id]
        
        if action:
            filtered_logs = [log for log in filtered_logs if log['action'] == action]
        
        if start_date:
            filtered_logs = [log for log in filtered_logs if log['timestamp'] >= start_date]
        
        if end_date:
            filtered_logs = [log for log in filtered_logs if log['timestamp'] <= end_date]
        
        return filtered_logs

# Decorators bảo mật
def rate_limit(max_requests=100, window=3600, per='ip'):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if per == 'ip':
                identifier = request.remote_addr
            elif per == 'user':
                identifier = getattr(g, 'user_id', request.remote_addr)
            else:
                identifier = request.remote_addr
            
            limiter = RateLimiter(max_requests, window)
            
            if not limiter.is_allowed(identifier):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_https(f):
    """Yêu cầu HTTPS"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not request.headers.get('X-Forwarded-Proto') == 'https':
            return jsonify({'error': 'HTTPS required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def validate_input(rules):
    """Input validation decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or request.form.to_dict()
            validator = InputValidator()
            errors = []
            
            for field, rule in rules.items():
                value = data.get(field)
                
                if rule.get('required') and not value:
                    errors.append(f"{field} is required")
                    continue
                
                if value and rule.get('type') == 'email':
                    if not validator.validate_email(value):
                        errors.append(f"{field} is not a valid email")
                
                if value and rule.get('type') == 'phone':
                    if not validator.validate_phone(value):
                        errors.append(f"{field} is not a valid phone number")
                
                if value and rule.get('type') == 'date':
                    if not validator.validate_date(value):
                        errors.append(f"{field} is not a valid date")
                
                if value and rule.get('max_length'):
                    if len(str(value)) > rule['max_length']:
                        errors.append(f"{field} exceeds maximum length")
            
            if errors:
                return jsonify({'errors': errors}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_security_event(event_type):
    """Log security event decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            monitor = SecurityMonitor()
            
            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                monitor.log_suspicious_activity(
                    'EXCEPTION',
                    str(e),
                    request.remote_addr
                )
                raise
        return decorated_function
    return decorator

def audit_log(action, resource):
    """Audit log decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            audit = SecurityAudit()
            user_id = getattr(g, 'user_id', None)
            
            # Lấy giá trị cũ nếu có
            old_value = None
            if hasattr(g, 'old_values'):
                old_value = g.old_values
            
            result = f(*args, **kwargs)
            
            # Lấy giá trị mới
            new_value = None
            if hasattr(g, 'new_values'):
                new_value = g.new_values
            
            audit.log_audit_event(user_id, action, resource, old_value, new_value)
            
            return result
        return decorated_function
    return decorator

# Security utilities
def generate_secure_token(length=32):
    """Tạo token bảo mật"""
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data):
    """Hash dữ liệu nhạy cảm"""
    return hashlib.sha256(data.encode()).hexdigest()

def check_password_strength(password):
    """Kiểm tra độ mạnh mật khẩu"""
    import re
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    
    return True, "Password is strong"

def sanitize_filename(filename):
    """Làm sạch tên file"""
    import re
    
    # Loại bỏ các ký tự nguy hiểm
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Giới hạn độ dài
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

# Security configuration
SECURITY_CONFIG = {
    'RATE_LIMIT_REQUESTS': 100,
    'RATE_LIMIT_WINDOW': 3600,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 300,
    'SESSION_TIMEOUT': 3600,
    'PASSWORD_MIN_LENGTH': 8,
    'REQUIRE_HTTPS': True,
    'ENABLE_CSRF': True,
    'ENABLE_AUDIT': True,
    'LOG_LEVEL': 'INFO'
}

def init_security_middleware(app):
    """Khởi tạo security middleware"""
    
    # Thêm security headers
    app.after_request(SecurityHeaders.add_security_headers)
    
    # Khởi tạo các components
    rate_limiter = RateLimiter()
    security_monitor = SecurityMonitor()
    input_validator = InputValidator()
    security_audit = SecurityAudit()
    
    return {
        'rate_limiter': rate_limiter,
        'security_monitor': security_monitor,
        'input_validator': input_validator,
        'security_audit': security_audit
    }
