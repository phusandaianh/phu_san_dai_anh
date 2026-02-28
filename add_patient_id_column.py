#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to add patient_id column to Patient table if it doesn't exist
"""

import sys
import os
import io

# Fix UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

def add_patient_id_column():
    """Add patient_id column to Patient table if it doesn't exist"""
    print("=" * 70)
    print("THÊM CỘT PATIENT_ID")
    print("=" * 70)
    print()
    
    try:
        # Try to query the column to check if it exists
        result = db.session.execute(db.text("PRAGMA table_info(patient)"))
        columns = [row[1] for row in result]
        
        if 'patient_id' in columns:
            print("✅ Cột patient_id đã tồn tại!")
            return True
        
        print("Cột patient_id chưa tồn tại, đang thêm...")
        
        # Add the column
        db.session.execute(db.text("""
            ALTER TABLE patient 
            ADD COLUMN patient_id VARCHAR(20) UNIQUE
        """))
        
        db.session.commit()
        print("✅ Đã thêm cột patient_id thành công!")
        print()
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Lỗi: {str(e)}")
        print()
        return False

if __name__ == '__main__':
    with app.app_context():
        add_patient_id_column()

