#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo tài khoản admin cho Phòng khám Đại Anh
Tài khoản: daihn
Mật khẩu: 190514@Da
"""

from app import app, db, User, Role
import werkzeug.security

def create_admin_account():
    """Tạo hoặc cập nhật tài khoản admin"""
    with app.app_context():
        try:
            # Tạo bảng nếu chưa có
            db.create_all()
            
            # Tạo roles nếu chưa có
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Quản trị viên hệ thống')
                db.session.add(admin_role)
                db.session.commit()
                print("Đã tạo role admin")
            
            # Kiểm tra tài khoản admin đã tồn tại chưa
            existing_admin = User.query.filter_by(username='daihn').first()
            
            if existing_admin:
                # Cập nhật tài khoản admin hiện có
                existing_admin.password_hash = werkzeug.security.generate_password_hash('190514@Da')
                existing_admin.full_name = 'Phòng khám Đại Anh - Admin'
                existing_admin.email = 'admin@phongkhamdaianh.com'
                existing_admin.status = 'active'
                
                # Xóa tất cả roles cũ và thêm role admin
                existing_admin.roles.clear()
                existing_admin.roles.append(admin_role)
                
                db.session.commit()
                print("✅ Đã cập nhật tài khoản admin: daihn")
            else:
                # Tạo tài khoản admin mới
                admin = User(
                    username='daihn',
                    password_hash=werkzeug.security.generate_password_hash('190514@Da'),
                    full_name='Phòng khám Đại Anh - Admin',
                    email='admin@phongkhamdaianh.com',
                    status='active'
                )
                admin.roles.append(admin_role)
                db.session.add(admin)
                db.session.commit()
                print("✅ Đã tạo tài khoản admin mới: daihn")
            
            print("🔐 Thông tin đăng nhập:")
            print("   Tên đăng nhập: daihn")
            print("   Mật khẩu: 190514@Da")
            print("   Email: admin@phongkhamdaianh.com")
            print("   Vai trò: Admin")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Lỗi khi tạo tài khoản admin: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    print("🚀 Đang tạo tài khoản admin cho Phòng khám Đại Anh...")
    success = create_admin_account()
    if success:
        print("✅ Hoàn thành!")
    else:
        print("❌ Có lỗi xảy ra!")
