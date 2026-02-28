# -*- coding: utf-8 -*-
"""
API Appointments - Lịch hẹn khám
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

appointments_bp = Blueprint('appointments', __name__)


def _appointment_to_json(a):
    """Chuyển appointment sang dict - format tương thích frontend"""
    doctor_name = getattr(a, 'doctor_name', None) or 'PK Đại Anh'
    p = a.patient
    return {
        'id': a.id,
        'patient_id': p.id if p else a.patient_id,
        'patient_pid': p.patient_id if p and p.patient_id else None,
        'patient_name': p.name if p else None,
        'patient_phone': p.phone if p else None,
        'patient_dob': p.date_of_birth.isoformat() if p and p.date_of_birth else None,
        'patient_address': p.address if p else None,
        'appointment_date': a.appointment_date.isoformat() if a.appointment_date else None,
        'service_type': a.service_type,
        'status': a.status,
        'doctor_name': doctor_name
    }


@appointments_bp.route('/today', methods=['GET'])
def get_today():
    """GET /api/appointments/today - Lịch khám hôm nay"""
    from app import db, Appointment, ensure_appointment_doctor_column
    
    ensure_appointment_doctor_column()
    today = datetime.now().date()
    q = (request.args.get('q') or '').strip()
    
    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today
    ).order_by(Appointment.appointment_date).all()
    
    if q:
        q_lower = q.lower()
        q_digits = ''.join(ch for ch in q if ch.isdigit())
        def match(a):
            try:
                name = (a.patient.name or '').lower()
                phone = (a.patient.phone or '')
                phone_digits = ''.join(ch for ch in phone if ch.isdigit())
                if q_lower in name: return True
                if q_lower in phone.lower(): return True
                if q_digits and q_digits in phone_digits: return True
            except Exception:
                pass
            return False
        appointments = [a for a in appointments if match(a)]
    
    return jsonify([_appointment_to_json(a) for a in appointments])


@appointments_bp.route('/by-date', methods=['GET'])
def get_by_date():
    """GET /api/appointments/by-date?date=yyyy-mm-dd"""
    from app import db, Appointment, ensure_appointment_doctor_column
    
    ensure_appointment_doctor_column()
    date_str = (request.args.get('date') or '').strip()
    if not date_str:
        return jsonify({'error': 'Thiếu tham số date'}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Định dạng ngày không hợp lệ (yyyy-mm-dd)'}), 400
    
    q = (request.args.get('q') or '').strip()
    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == target_date
    ).order_by(Appointment.appointment_date).all()
    
    if q:
        q_lower = q.lower()
        q_digits = ''.join(ch for ch in q if ch.isdigit())
        def match(a):
            try:
                name = (a.patient.name or '').lower()
                phone = (a.patient.phone or '')
                phone_digits = ''.join(ch for ch in phone if ch.isdigit())
                if q_lower in name: return True
                if q_lower in phone.lower(): return True
                if q_digits and q_digits in phone_digits: return True
            except Exception:
                pass
            return False
        appointments = [a for a in appointments if match(a)]
    
    return jsonify([_appointment_to_json(a) for a in appointments])


@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
def get_one(appointment_id):
    """GET /api/appointments/<id>"""
    from app import Appointment
    
    a = Appointment.query.get_or_404(appointment_id)
    return jsonify(_appointment_to_json(a))


@appointments_bp.route('/<int:appointment_id>/diagnosis', methods=['GET'])
def get_diagnosis(appointment_id):
    """GET /api/appointments/<id>/diagnosis"""
    from app import MedicalRecord
    
    rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).order_by(MedicalRecord.id.desc()).first()
    return jsonify({'diagnosis': (rec.diagnosis if rec else '')})


@appointments_bp.route('/<int:appointment_id>/diagnosis', methods=['PUT'])
def update_diagnosis(appointment_id):
    """PUT /api/appointments/<id>/diagnosis"""
    from app import db, Appointment, MedicalRecord
    
    data = request.json or {}
    text = (data.get('diagnosis') or '').strip()
    appt = Appointment.query.get_or_404(appointment_id)
    rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    if not rec:
        rec = MedicalRecord(patient_id=appt.patient_id, appointment_id=appointment_id)
        db.session.add(rec)
    rec.diagnosis = text
    db.session.commit()
    return jsonify({'diagnosis': rec.diagnosis})


@appointments_bp.route('/<int:appointment_id>/notes', methods=['GET'])
def get_notes(appointment_id):
    """GET /api/appointments/<id>/notes"""
    from app import MedicalRecord
    
    rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).order_by(MedicalRecord.id.desc()).first()
    return jsonify({'notes': (rec.notes if rec else '')})


@appointments_bp.route('/<int:appointment_id>/notes', methods=['PUT'])
def update_notes(appointment_id):
    """PUT /api/appointments/<id>/notes"""
    from app import db, Appointment, MedicalRecord
    
    data = request.json or {}
    text = (data.get('notes') or '').strip()
    appt = Appointment.query.get_or_404(appointment_id)
    rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    if not rec:
        rec = MedicalRecord(patient_id=appt.patient_id, appointment_id=appointment_id)
        db.session.add(rec)
    rec.notes = text
    db.session.commit()
    return jsonify({'notes': rec.notes})
