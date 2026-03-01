# -*- coding: utf-8 -*-
"""
API Auth - Đăng nhập, token
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import text
from collections import defaultdict
from time import time
import werkzeug
import secrets

auth_bp = Blueprint('auth', __name__)

# Rate limit theo IP cho login (tránh brute-force)
_LOGIN_RATE = defaultdict(list)
_LOGIN_WINDOW = 60
_LOGIN_MAX = 15  # tang len de tranh khoa khi thu nhieu

def _check_login_rate_limit():
    ip = request.remote_addr or 'unknown'
    now = time()
    _LOGIN_RATE[ip] = [t for t in _LOGIN_RATE[ip] if now - t < _LOGIN_WINDOW]
    if len(_LOGIN_RATE[ip]) >= _LOGIN_MAX:
        return True  # over limit
    _LOGIN_RATE[ip].append(now)
    return False


@auth_bp.route('/login', methods=['POST'])  # Full path: /api/login
def login():
    """POST /api/auth/login - Đăng nhập, trả về token"""
    if _check_login_rate_limit():
        return jsonify({'error': 'Quá nhiều lần đăng nhập. Vui lòng thử lại sau vài phút.'}), 429
    from app import db, register_token
    
    data = request.get_json(silent=True) or request.form or {}
    username = (data.get('username') or '').strip()
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    try:
        result = db.session.execute(
            text("SELECT id, username, password_hash, full_name, email, status FROM user WHERE username = :username"),
            {"username": username}
        ).fetchone()
        
        if not result:
            return jsonify({'error': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401
        
        user_id, username_db, password_hash, full_name, email, status = result
        
        if not werkzeug.security.check_password_hash(password_hash, password):
            return jsonify({'error': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401
        
        if status != 'active':
            return jsonify({'error': 'Tài khoản đã bị vô hiệu hóa'}), 401
        
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.execute(
            text("UPDATE user SET last_login = :now WHERE id = :user_id"),
            {"now": now_str, "user_id": user_id}
        )
        db.session.commit()
        
        roles_result = db.session.execute(
            text("SELECT r.name FROM role r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        roles = [row[0] for row in roles_result]
        
        token = secrets.token_urlsafe(32)
        register_token(token, user_id)
        
        resp = jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'username': username_db,
                'full_name': full_name or '',
                'email': email or '',
                'roles': roles
            }
        })
        # Cookie để kiểm tra khi phục vụ trang staff (HTML)
        resp.set_cookie(
            'auth_token', token,
            httponly=True,
            samesite='Lax',
            max_age=3600
        )
        return resp
    except Exception as e:
        import traceback
        traceback.print_exc()
        from flask import current_app
        err_detail = str(e) if current_app.config.get('DEBUG') else None
        return jsonify({'error': 'Lỗi hệ thống', 'detail': err_detail}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """POST /api/logout - Xóa cookie auth"""
    resp = jsonify({'message': 'Đã đăng xuất'})
    resp.set_cookie('auth_token', '', max_age=0, expires=0)
    return resp
