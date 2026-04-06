#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gán PID cho bệnh nhân đang thiếu patient_id, dùng cùng quy tắc với app.generate_patient_id:
BN + 2 số cuối năm + 5 số thứ tự (vd BN2600001).
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from app import app, db, Patient, generate_patient_id


def update_old_patients():
    with app.app_context():
        print("=" * 70)
        print("CẬP NHẬT PID CHO BỆNH NHÂN CŨ (định dạng BNyy#####)")
        print("=" * 70)
        print()

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
                new_pid = generate_patient_id(patient.phone)
                patient.patient_id = new_pid
                db.session.flush()
                updated_count += 1
                print(f"✅ Cập nhật: {patient.name} ({patient.phone}) → PID: {new_pid}")
            except Exception as e:
                error_count += 1
                print(f"❌ Lỗi khi cập nhật {patient.name} ({patient.phone}): {str(e)}")

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
            print(f"Lỗi commit: {e}")
            print("=" * 70)


if __name__ == '__main__':
    update_old_patients()
