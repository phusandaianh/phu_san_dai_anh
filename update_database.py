#!/usr/bin/env python3
"""
Script cập nhật database để thêm cột đồng bộ Voluson E10
"""

import sqlite3
import os

def update_database():
    """Cập nhật database để thêm cột voluson_synced"""
    print("🔧 Cập nhật database cho đồng bộ Voluson E10...")
    
    try:
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        
        # Kiểm tra cột voluson_synced đã tồn tại chưa
        cursor.execute("PRAGMA table_info(appointment)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'voluson_synced' not in columns:
            print("➕ Thêm cột voluson_synced...")
            cursor.execute("ALTER TABLE appointment ADD COLUMN voluson_synced INTEGER DEFAULT 0")
            print("✅ Đã thêm cột voluson_synced")
        else:
            print("✅ Cột voluson_synced đã tồn tại")
            
        if 'voluson_sync_time' not in columns:
            print("➕ Thêm cột voluson_sync_time...")
            cursor.execute("ALTER TABLE appointment ADD COLUMN voluson_sync_time DATETIME")
            print("✅ Đã thêm cột voluson_sync_time")
        else:
            print("✅ Cột voluson_sync_time đã tồn tại")
        
        conn.commit()
        conn.close()
        
        print("🎉 Cập nhật database thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi cập nhật database: {e}")
        return False

if __name__ == "__main__":
    update_database()
