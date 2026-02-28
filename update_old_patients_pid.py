#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to update existing patients without patient_id (PID) to have a unique PID
based on their phone number following the same logic as generate_patient_id()
"""

import sys
import os
import io

# Fix UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Patient

def generate_patient_id(phone):
    """
    Generate a unique patient_id based on phone number.
    Format: phone_number + suffix_number if duplicate exists
    Example: '0987654321', '09876543211', '09876543212', ...
    """
    # Base PID is the phone number itself
    base_pid = phone
    
    # Check if base PID already exists
    existing_patient = Patient.query.filter_by(patient_id=base_pid).first()
    if not existing_patient:
        return base_pid
    
    # If exists, try with suffix starting from 1
    suffix = 1
    while True:
        new_pid = f"{phone}{suffix}"
        existing_patient = Patient.query.filter_by(patient_id=new_pid).first()
        if not existing_patient:
            return new_pid
        suffix += 1
        # Safety check to prevent infinite loop
        if suffix > 999:
            # Fallback: use timestamp if somehow all combinations are taken
            from datetime import datetime
            return f"{phone}_{int(datetime.utcnow().timestamp())}"

def update_old_patients():
    """Update patients without patient_id to have a unique PID"""
    print("=" * 70)
    print("CẬP NHẬT PID CHO BỆNH NHÂN CŨ")
    print("=" * 70)
    print()
    
    # Find all patients without patient_id
    patients_without_pid = Patient.query.filter(
        (Patient.patient_id == None) | (Patient.patient_id == '')
    ).all()
    
    if not patients_without_pid:
        print("✅ Tất cả bệnh nhân đã có PID!")
        return
    
    print(f"Tìm thấy {len(patients_without_pid)} bệnh nhân chưa có PID")
    print()
    
    updated_count = 0
    error_count = 0
    
    for patient in patients_without_pid:
        try:
            # Generate unique PID for this patient
            new_pid = generate_patient_id(patient.phone)
            
            # Update patient
            patient.patient_id = new_pid
            updated_count += 1
            
            print(f"✅ Cập nhật: {patient.name} ({patient.phone}) → PID: {new_pid}")
            
        except Exception as e:
            error_count += 1
            print(f"❌ Lỗi khi cập nhật {patient.name} ({patient.phone}): {str(e)}")
    
    # Commit all changes
    try:
        db.session.commit()
        print()
        print("=" * 70)
        print("KẾT QUẢ")
        print("=" * 70)
        print(f"✅ Cập nhật thành công: {updated_count} bệnh nhân")
        if error_count > 0:
            print(f"❌ Lỗi: {error_count} bệnh nhân")
        print()
        print("Hoàn tất!")
    except Exception as e:
        db.session.rollback()
        print()
        print("=" * 70)
        print("LỖI")
        print("=" * 70)
        print(f"❌ Lỗi khi commit: {str(e)}")
        print()
        sys.exit(1)

if __name__ == '__main__':
    with app.app_context():
        update_old_patients()

