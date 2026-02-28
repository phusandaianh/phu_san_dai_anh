#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tạo appointment test để kiểm tra đồng bộ worklist
"""

from datetime import datetime
from app import app, db, Patient, Appointment

with app.app_context():
    # Xóa appointment cũ nếu có
    today = datetime.now().date()
    old_appts = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today
    ).all()
    for appt in old_appts:
        db.session.delete(appt)
    db.session.commit()
    
    # Tạo bệnh nhân mới
    patient = Patient(
        patient_id='TEST001',
        name='Nguyễn Thị Test',
        phone='0987654321',
        address='123 Đường Test',
        date_of_birth=datetime(1990, 5, 15).date()
    )
    db.session.add(patient)
    db.session.commit()
    
    # Tạo appointment hôm nay
    from datetime import timedelta
    now = datetime.now()
    appointment_time = now.replace(hour=14, minute=30, second=0, microsecond=0)
    
    appointment = Appointment(
        patient_id=patient.id,
        appointment_date=appointment_time,
        service_type='Siêu âm thai'
    )
    db.session.add(appointment)
    db.session.commit()
    
    print(f"✓ Đã tạo appointment test:")
    print(f"  - Bệnh nhân: {patient.name}")
    print(f"  - Phone: {patient.phone}")
    print(f"  - Patient ID: {patient.patient_id}")
    print(f"  - Thời gian: {appointment_time}")
    print(f"  - Dịch vụ: {appointment.service_type}")
    print(f"\nBây giờ chạy: python mwl_sync.py")
