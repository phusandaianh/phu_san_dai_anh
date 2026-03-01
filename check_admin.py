#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kiem tra tai khoan admin va thu dang nhap"""
from app import app, db
from sqlalchemy import text
import werkzeug.security

with app.app_context():
    for uname in ['admin', 'daihn']:
        r = db.session.execute(
            text("SELECT id, username, password_hash, full_name, status FROM user WHERE username = :u"),
            {"u": uname}
        ).fetchone()
        if not r:
            print(f"{uname}: KHONG TON TAI")
            continue
        uid, username, ph, fn, status = r
        roles = db.session.execute(
            text("SELECT r.name FROM role r JOIN user_roles ur ON r.id=ur.role_id WHERE ur.user_id=:uid"),
            {"uid": uid}
        ).fetchall()
        roles = [x[0] for x in roles]
        ok = werkzeug.security.check_password_hash(ph, '190514@Da')
        print(f"{uname}: status={status}, roles={roles}, password_ok={ok}")
