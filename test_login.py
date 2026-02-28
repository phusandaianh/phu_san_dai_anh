#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test đăng nhập admin
"""

import requests
import json

def test_login():
    """Test đăng nhập admin"""
    try:
        url = "http://127.0.0.1:5000/api/login"
        data = {
            "username": "daihn",
            "password": "190514@Da"
        }
        
        response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Đăng nhập thành công!")
            print(f"Token: {result.get('token', 'N/A')}")
            print(f"User: {result.get('user', {})}")
        else:
            print("❌ Đăng nhập thất bại!")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == '__main__':
    print("🧪 Test đăng nhập admin...")
    test_login()
