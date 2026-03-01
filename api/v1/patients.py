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
    from app import db, Patient, _get_or_404
    
    data = request.json or {}
    p = _get_or_404(Patient, patient_id)
    name = (data.get('name') or '').strip()
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
    """GET /api/patients/by-phone?phone=xxx - Tìm bệnh nhân theo SĐT"""
    from app import Patient
    
    phone = (request.args.get('phone') or '').strip()
    if not phone:
        return jsonify({'message': 'Thiếu tham số phone'}), 400
    
    patient = Patient.query.filter_by(phone=phone).first()
    if not patient:
        return jsonify({'found': False})
    
    return jsonify({
        'found': True,
        'id': patient.id,
        'name': patient.name,
        'phone': patient.phone,
        'address': patient.address,
        'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None
    })
