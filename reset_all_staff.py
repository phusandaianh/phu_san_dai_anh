#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset mat khau TAT CA tai khoan nhan vien ve mat khau mac dinh
Chay: python reset_all_staff.py
"""

from app import app, db
from sqlalchemy import text
import werkzeug.security

# Mat khau mac dinh cho tat ca tai khoan nhan vien
DEFAULT_PASSWORD = '190514@Da'

STAFF_ACCOUNTS = ['admin', 'daihn', 'bacsi', 'dieuduong']

def main():
    with app.app_context():
        try:
            password_hash = werkzeug.security.generate_password_hash(DEFAULT_PASSWORD, method='pbkdf2:sha256', salt_length=16)
            updated = []

            for username in STAFF_ACCOUNTS:
                r = db.session.execute(
                    text("UPDATE user SET password_hash = :ph WHERE username = :u"),
                    {"ph": password_hash, "u": username}
                )
                if r.rowcount > 0:
                    updated.append(username)

            db.session.commit()

            if updated:
                print("Da reset mat khau thanh cong!")
                print("Tai khoan:", ", ".join(updated))
                print("Mat khau mac dinh:", DEFAULT_PASSWORD)
                print("Dang nhap tai: /users.html")
            else:
                print("Khong tim thay tai khoan nao.")
                print("Dang nhap /users.html bang admin hoac daihn, tao staff qua giao dien. Hoac chay create_admin_daihn.py de tao daihn.")

        except Exception as e:
            db.session.rollback()
            print("Loi:", e)
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
