#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reset mat khau tai khoan admin
Chay: python reset_admin.py
"""

from app import app, db
from sqlalchemy import text
import werkzeug.security

DEFAULT_PASSWORD = '190514@Da'

def reset_admin():
    with app.app_context():
        try:
            password_hash = werkzeug.security.generate_password_hash(DEFAULT_PASSWORD)
            updated = []

            # Reset admin
            r = db.session.execute(
                text("UPDATE user SET password_hash = :ph WHERE username = 'admin'"),
                {"ph": password_hash}
            )
            if r.rowcount > 0:
                updated.append("admin")

            # Reset daihn
            r = db.session.execute(
                text("UPDATE user SET password_hash = :ph WHERE username = 'daihn'"),
                {"ph": password_hash}
            )
            if r.rowcount > 0:
                updated.append("daihn")

            db.session.commit()

            if updated:
                print("Da reset mat khau thanh cong!")
                print("Tai khoan:", ", ".join(updated))
                print("Mat khau:  ", DEFAULT_PASSWORD)
                print("Dang nhap tai: /users.html")
            else:
                print("Khong tim thay tai khoan admin hoac daihn.")
                print("Chay fix_admin.py de tao tai khoan daihn.")

        except Exception as e:
            db.session.rollback()
            print("Loi:", e)
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    reset_admin()
