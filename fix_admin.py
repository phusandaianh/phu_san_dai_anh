#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sửa lỗi và tạo tài khoản admin
"""

from app import app, db
from sqlalchemy import text
import werkzeug.security

def fix_admin():
    """Sửa lỗi và tạo admin"""
    with app.app_context():
        try:
            db.create_all()
            
            db.session.execute(text("DELETE FROM user_roles WHERE user_id IN (SELECT id FROM user WHERE username = 'daihn')"))
            db.session.execute(text("DELETE FROM user WHERE username = 'daihn'"))
            db.session.commit()
            print("Đã xóa tài khoản admin cũ")
            
            db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('admin', 'Quản trị viên hệ thống')"))
            db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('doctor', 'Bác sĩ')"))
            db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('nurse', 'Y tá')"))
            db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('receptionist', 'Lễ tân')"))
            db.session.commit()
            print("Đã tạo các roles")
            
            password_hash = werkzeug.security.generate_password_hash('190514@Da')
            db.session.execute(
                text("INSERT INTO user (username, password_hash, full_name, email, status, created_at) VALUES ('daihn', :password_hash, 'Phòng khám Đại Anh - Admin', 'admin@phongkhamdaianh.com', 'active', datetime('now'))"),
                {"password_hash": password_hash}
            )
            db.session.commit()
            print("Đã tạo tài khoản admin")
            
            admin_id = db.session.execute(text("SELECT id FROM user WHERE username = 'daihn'")).fetchone()[0]
            admin_role_id = db.session.execute(text("SELECT id FROM role WHERE name = 'admin'")).fetchone()[0]
            
            db.session.execute(
                text("INSERT INTO user_roles (user_id, role_id) VALUES (:admin_id, :admin_role_id)"),
                {"admin_id": admin_id, "admin_role_id": admin_role_id}
            )
            db.session.commit()
            print("Đã gán role admin")
            
            print("✅ Hoàn thành!")
            print("🔐 Thông tin đăng nhập:")
            print("   Tên đăng nhập: daihn")
            print("   Mật khẩu: 190514@Da")
            print("   Email: admin@phongkhamdaianh.com")
            print("   Vai trò: Admin")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("🔧 Đang sửa lỗi và tạo tài khoản admin...")
    fix_admin()
