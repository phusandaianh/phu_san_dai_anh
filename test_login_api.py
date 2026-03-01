#!/usr/bin/env python3
"""Test login API"""
import sys
sys.path.insert(0, '.')
from app import app
with app.test_client() as c:
    r = c.post('/api/login', json={'username':'admin','password':'190514@Da'})
    print('Status:', r.status_code)
    j = r.get_json()
    print('OK:', r.status_code == 200)
    if j: print('Has token:', 'token' in j)
