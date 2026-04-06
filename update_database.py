#!/usr/bin/env python3
"""
Script cập nhật database để thêm cột đồng bộ máy siêu âm
"""

import sqlite3
import os

def update_database():
    """Cập nhật database cho trạng thái đồng bộ máy siêu âm (giữ cột legacy)."""
    print("🔧 Cập nhật database cho đồng bộ máy siêu âm...")
    
    try:
        conn = sqlite3.connect('clinic.db')
        cursor = conn.cursor()
        
        # Kiểm tra các cột legacy đã tồn tại chưa
        cursor.execute("PRAGMA table_info(appointment)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'Maysieuam_synced' not in columns:
            print("➕ Thêm cột đồng bộ legacy: Maysieuam_synced...")
            cursor.execute("ALTER TABLE appointment ADD COLUMN Maysieuam_synced INTEGER DEFAULT 0")
            print("✅ Đã thêm cột đồng bộ legacy: Maysieuam_synced")
        else:
            print("✅ Cột đồng bộ legacy Maysieuam_synced đã tồn tại")
            
        if 'Maysieuam_sync_time' not in columns:
            print("➕ Thêm cột thời gian đồng bộ legacy: Maysieuam_sync_time...")
            cursor.execute("ALTER TABLE appointment ADD COLUMN Maysieuam_sync_time DATETIME")
            print("✅ Đã thêm cột thời gian đồng bộ legacy: Maysieuam_sync_time")
        else:
            print("✅ Cột thời gian đồng bộ legacy Maysieuam_sync_time đã tồn tại")
        
        conn.commit()
        conn.close()
        
        print("🎉 Cập nhật database thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi cập nhật database: {e}")
        return False

if __name__ == "__main__":
    update_database()
