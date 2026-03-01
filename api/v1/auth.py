# -*- coding: utf-8 -*-
"""
API Auth - Đăng nhập, token
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import text
import werkzeug
import secrets

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])  # Full path: /api/login
def login():
    """POST /api/auth/login - Đăng nhập, trả về token"""
    from app import db, register_token
    
    data = request.json or {}
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
        
        db.session.execute(
            text("UPDATE user SET last_login = :now WHERE id = :user_id"),
            {"now": datetime.utcnow(), "user_id": user_id}
        )
        db.session.commit()
        
        roles_result = db.session.execute(
            text("SELECT r.name FROM role r JOIN user_roles ur ON r.id = ur.role_id WHERE ur.user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        roles = [row[0] for row in roles_result]
        
        token = secrets.token_urlsafe(32)
        register_token(token, user_id)
        
        return jsonify({
            'token': token,
            'user': {
                'id': user_id,
                'username': username_db,
                'full_name': full_name,
                'email': email,
                'roles': roles
            }
        })
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Lỗi hệ thống'}), 500
