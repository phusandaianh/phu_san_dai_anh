#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo tài khoản Admin, Bác sĩ, Điều dưỡng với phân quyền
Chạy: python create_staff_accounts.py
"""

from app import app, db
from sqlalchemy import text
import werkzeug.security
import secrets
import string


def random_password(length=12):
    """Tạo mật khẩu ngẫu nhiên an toàn"""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def ensure_roles():
    """Đảm bảo các role tồn tại"""
    db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('admin', 'Quản trị viên hệ thống')"))
    db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('doctor', 'Bác sĩ')"))
    db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('nurse', 'Điều dưỡng')"))
    db.session.execute(text("INSERT OR IGNORE INTO role (name, description) VALUES ('receptionist', 'Lễ tân')"))
    db.session.commit()
    print("[OK] Da tao/kiem tra cac role: admin, doctor, nurse, receptionist")


def create_user_if_not_exists(username, password, full_name, email, role_name):
    """Tạo user nếu chưa tồn tại (theo username hoặc email), gán role"""
    row = db.session.execute(
        text("SELECT id FROM user WHERE username = :u OR email = :e"),
        {"u": username, "e": email}
    ).fetchone()
    if row:
        print(f"   Tai khoan {username} hoac email da ton tai, bo qua")
        return False

    password_hash = werkzeug.security.generate_password_hash(password)
    db.session.execute(
        text("""
            INSERT INTO user (username, password_hash, full_name, email, status, created_at)
            VALUES (:u, :ph, :fn, :em, 'active', datetime('now'))
        """),
        {"u": username, "ph": password_hash, "fn": full_name, "em": email}
    )
    db.session.commit()

    user_id = db.session.execute(text("SELECT id FROM user WHERE username = :u"), {"u": username}).fetchone()[0]
    role_id = db.session.execute(text("SELECT id FROM role WHERE name = :r"), {"r": role_name}).fetchone()[0]
    db.session.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)"),
        {"uid": user_id, "rid": role_id}
    )
    db.session.commit()
    return True


def main():
    print("=" * 60)
    print("  TAO TAI KHOAN NHAN VIEN - Phong kham Dai Anh")
    print("=" * 60)

    with app.app_context():
        try:
            db.create_all()
            ensure_roles()

            accounts = [
                # admin - toàn quyền quản trị
                {
                    "username": "admin",
                    "password": random_password(),
                    "full_name": "Quan tri vien",
                    "email": "admin@pkdaianh.local",
                    "role": "admin",
                },
                # bác sĩ - khám, kê đơn, xem hồ sơ
                {
                    "username": "bacsi",
                    "password": random_password(),
                    "full_name": "Bac si kham benh",
                    "email": "bacsi@pkdaianh.local",
                    "role": "doctor",
                },
                # điều dưỡng - danh sách khám, xét nghiệm, hồ sơ
                {
                    "username": "dieuduong",
                    "password": random_password(),
                    "full_name": "Dieu duong",
                    "email": "dieuduong@pkdaianh.local",
                    "role": "nurse",
                },
            ]

            created = []
            for acc in accounts:
                if create_user_if_not_exists(
                    acc["username"], acc["password"],
                    acc["full_name"], acc["email"],
                    acc["role"]
                ):
                    created.append(acc)

            print("\n" + "=" * 60)
            print("  THONG TIN DANG NHAP")
            print("=" * 60)
            for acc in accounts:
                is_new = acc in created
                print(f"\n  [{acc['role'].upper()}] {acc['full_name']}")
                print(f"    Ten dang nhap: {acc['username']}")
                if is_new:
                    print(f"    Mat khau:      {acc['password']}  (LUU LAI, doi ngay sau lan dau)")
                else:
                    print(f"    Mat khau:      (da ton tai - doi qua /users.html neu quen)")
                print(f"    Email:         {acc['email']}")

            if created:
                print(f"\n[OK] Da tao {len(created)} tai khoan moi")
            else:
                print("\n[OK] Tat ca tai khoan da ton tai")

            print("\nDang nhap tai: /users.html")
            print("Benh nhan chi dung: /booking.html va /schedule.html de dat lich")
            print("=" * 60)

        except Exception as e:
            db.session.rollback()
            print(f"Loi: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
