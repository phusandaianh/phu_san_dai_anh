# -*- coding: utf-8 -*-
"""
API Patients - CRUD bệnh nhân
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import re

patients_bp = Blueprint('patients', __name__)


@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """GET /api/patients/<id> - Chi tiết bệnh nhân"""
    from app import Patient, _get_or_404
    
    p = _get_or_404(Patient, patient_id)
    return jsonify({
        'id': p.id,
        'name': p.name,
        'phone': p.phone,
        'address': p.address,
        'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else None
    })


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """PUT /api/patients/<id> - Cập nhật bệnh nhân"""
    from app import db, Patient, _get_or_404, normalize_patient_display_name
    
    data = request.json or {}
    p = _get_or_404(Patient, patient_id)
    name = normalize_patient_display_name(data.get('name') or '')
    phone = (data.get('phone') or '').strip()
    address = (data.get('address') or '').strip()
    dob = (data.get('date_of_birth') or '').strip()
    
    if not name or not phone:
        return jsonify({'message': 'Vui lòng nhập đầy đủ họ tên và số điện thoại.'}), 400
    if not re.match(r'^\d{10,11}$', phone):
        return jsonify({'message': 'Số điện thoại không hợp lệ (10-11 số).'}), 400
    
    try:
        p.name = name
        p.phone = phone
        p.address = address or None
        p.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật thông tin bệnh nhân'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật bệnh nhân: {str(e)}'}), 500


@patients_bp.route('/by-phone', methods=['GET'])
def get_by_phone():
    """GET /api/patients/by-phone?phone=xxx — Tất cả hồ sơ Patient gắn SĐT (có thể nhiều người)."""
    from app import Patient

    phone = (request.args.get('phone') or '').strip()
    if not phone:
        return jsonify({'message': 'Thiếu tham số phone'}), 400

    rows = (
        Patient.query.filter_by(phone=phone)
        .order_by(Patient.id.desc())
        .all()
    )
    if not rows:
        return jsonify({'found': False, 'patients': [], 'count': 0})

    def row_dict(p):
        return {
            'id': p.id,
            'patient_pid': p.patient_id or '',
            'name': p.name,
            'phone': p.phone,
            'address': p.address,
            'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else None,
        }

    patients = [row_dict(p) for p in rows]
    first = patients[0]
    return jsonify({
        'found': True,
        'count': len(patients),
        'patients': patients,
        'id': first['id'],
        'patient_pid': first['patient_pid'],
        'name': first['name'],
        'phone': first['phone'],
        'address': first['address'],
        'date_of_birth': first['date_of_birth'],
    })
