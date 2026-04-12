# -*- coding: utf-8 -*-
"""
API Appointments - Lịch hẹn khám
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy import or_

appointments_bp = Blueprint('appointments', __name__)


def _appointment_to_json(a):
    """Chuyển appointment sang dict - format tương thích frontend"""
    from app import MedicalRecord
    doctor_name = getattr(a, 'doctor_name', None) or 'PK Đại Anh'
    p = a.patient
    rec = MedicalRecord.query.filter_by(appointment_id=a.id).order_by(MedicalRecord.id.desc()).first()
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
        'diagnosis': (rec.diagnosis if rec else '') or '',
        'notes': (rec.notes if rec else '') or '',
        'doctor_name': doctor_name,
        'expected_delivery_date': a.expected_delivery_date.isoformat() if getattr(a, 'expected_delivery_date', None) else None
    }


@appointments_bp.route('/today', methods=['GET'])
def get_today():
    """GET /api/appointments/today - Lịch khám hôm nay"""
    from app import db, Appointment, Patient, ensure_appointment_doctor_column, ensure_appointment_expected_delivery_date_column
    
    ensure_appointment_doctor_column()
    ensure_appointment_expected_delivery_date_column()
    today = datetime.now().date()

    name = (request.args.get('name') or '').strip()
    pid = (request.args.get('pid') or '').strip()
    phone = (request.args.get('phone') or '').strip()
    status = (request.args.get('status') or '').strip()
    q = (request.args.get('q') or '').strip()

    query = (
        Appointment.query
        .join(Patient, Appointment.patient_id == Patient.id)
        .filter(db.func.date(Appointment.appointment_date) == today)
    )

    if status:
        query = query.filter(Appointment.status == status)
    if name:
        query = query.filter(Patient.name.ilike(f'%{name}%'))
    if phone:
        query = query.filter(Patient.phone.ilike(f'%{phone}%'))
    if pid:
        query = query.filter(Patient.patient_id.ilike(f'%{pid}%'))

    # Backward-compatible: if only `q` is used, search name/phone/pid
    if q and not (name or pid or phone):
        q_lower = q.lower()
        q_digits = ''.join(ch for ch in q if ch.isdigit())
        conds = []
        if q_lower:
            conds.append(Patient.name.ilike(f'%{q_lower}%'))
            conds.append(Patient.phone.ilike(f'%{q_lower}%'))
        if q_digits:
            conds.append(Patient.phone.ilike(f'%{q_digits}%'))
            conds.append(Patient.patient_id.ilike(f'%{q_digits}%'))
        if conds:
            query = query.filter(or_(*conds))

    appointments = query.order_by(Appointment.appointment_date).all()
    return jsonify([_appointment_to_json(a) for a in appointments])


@appointments_bp.route('/from-today', methods=['GET'])
def get_from_today():
    """GET /api/appointments/from-today - Tất cả lịch khám từ hôm nay trở đi (tăng dần theo ngày/giờ)

    Query (tùy chọn):
    - start: yyyy-mm-dd (mặc định hôm nay)
    - end: yyyy-mm-dd — giới hạn ngày khám <= end
    - omit_cancelled: 1/true/yes — bỏ lịch status cancelled

    Để tránh lỗi context SQLAlchemy, hàm này chỉ dùng `Appointment.query`
    (không động tới `db.session` trực tiếp).
    """
    from datetime import date
    from app import db, Appointment, Patient, ensure_appointment_expected_delivery_date_column

    try:
        ensure_appointment_expected_delivery_date_column()
        today = date.today()

        # start (optional) to support filtering from tomorrow trở đi
        start_str = (request.args.get('start') or '').strip()  # yyyy-mm-dd
        if not start_str:
            start_date = today
        else:
            try:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Định dạng start không hợp lệ (yyyy-mm-dd)'}), 400

        name = (request.args.get('name') or '').strip()
        pid = (request.args.get('pid') or '').strip()
        phone = (request.args.get('phone') or '').strip()
        status = (request.args.get('status') or '').strip()
        q = (request.args.get('q') or '').strip()

        # from-today = appointment_date >= start of start_date
        start_dt = datetime.combine(start_date, datetime.min.time())

        query = (
            Appointment.query
            .join(Patient, Appointment.patient_id == Patient.id)
            .filter(Appointment.appointment_date >= start_dt)
        )

        # end (optional, yyyy-mm-dd): chỉ lấy lịch có ngày khám <= end (theo lịch)
        end_str = (request.args.get('end') or '').strip()
        if end_str:
            try:
                end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Định dạng end không hợp lệ (yyyy-mm-dd)'}), 400
            query = query.filter(db.func.date(Appointment.appointment_date) <= end_date)

        omit_cancelled = (request.args.get('omit_cancelled') or '').strip().lower() in ('1', 'true', 'yes')
        if omit_cancelled:
            query = query.filter(Appointment.status != 'cancelled')

        if status:
            query = query.filter(Appointment.status == status)
        if name:
            query = query.filter(Patient.name.ilike(f'%{name}%'))
        if phone:
            query = query.filter(Patient.phone.ilike(f'%{phone}%'))
        if pid:
            query = query.filter(Patient.patient_id.ilike(f'%{pid}%'))

        # Backward-compatible: if only `q` is used, search name/phone/pid
        if q and not (name or pid or phone):
            q_lower = q.lower()
            q_digits = ''.join(ch for ch in q if ch.isdigit())
            conds = []
            if q_lower:
                conds.append(Patient.name.ilike(f'%{q_lower}%'))
                conds.append(Patient.phone.ilike(f'%{q_lower}%'))
            if q_digits:
                conds.append(Patient.phone.ilike(f'%{q_digits}%'))
                conds.append(Patient.patient_id.ilike(f'%{q_digits}%'))
            if conds:
                query = query.filter(or_(*conds))

        appointments = query.order_by(Appointment.appointment_date).all()
        return jsonify([_appointment_to_json(a) for a in appointments])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@appointments_bp.route('/past', methods=['GET'])
def get_past():
    """GET /api/appointments/past?before=yyyy-mm-dd - Lịch khám trước một ngày (mặc định trước hôm nay)."""
    from app import db, Appointment, Patient, ensure_appointment_expected_delivery_date_column

    try:
        ensure_appointment_expected_delivery_date_column()

        before_str = (request.args.get('before') or '').strip()  # yyyy-mm-dd
        if not before_str:
            before_date = datetime.now().date()
        else:
            try:
                before_date = datetime.strptime(before_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Định dạng before không hợp lệ (yyyy-mm-dd)'}), 400

        before_dt = datetime.combine(before_date, datetime.min.time())

        name = (request.args.get('name') or '').strip()
        pid = (request.args.get('pid') or '').strip()
        phone = (request.args.get('phone') or '').strip()
        status = (request.args.get('status') or '').strip()
        q = (request.args.get('q') or '').strip()

        query = (
            Appointment.query
            .join(Patient, Appointment.patient_id == Patient.id)
            .filter(Appointment.appointment_date < before_dt)
        )

        if status:
            query = query.filter(Appointment.status == status)
        if name:
            query = query.filter(Patient.name.ilike(f'%{name}%'))
        if phone:
            query = query.filter(Patient.phone.ilike(f'%{phone}%'))
        if pid:
            query = query.filter(Patient.patient_id.ilike(f'%{pid}%'))

        # Backward-compatible: if only `q` is used, search name/phone/pid
        if q and not (name or pid or phone):
            q_lower = q.lower()
            q_digits = ''.join(ch for ch in q if ch.isdigit())
            conds = []
            if q_lower:
                conds.append(Patient.name.ilike(f'%{q_lower}%'))
                conds.append(Patient.phone.ilike(f'%{q_lower}%'))
            if q_digits:
                conds.append(Patient.phone.ilike(f'%{q_digits}%'))
                conds.append(Patient.patient_id.ilike(f'%{q_digits}%'))
            if conds:
                query = query.filter(or_(*conds))

        appointments = query.order_by(Appointment.appointment_date.desc()).all()
        return jsonify([_appointment_to_json(a) for a in appointments])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@appointments_bp.route('/by-date', methods=['GET'])
def get_by_date():
    """GET /api/appointments/by-date?date=yyyy-mm-dd"""
    from app import db, Appointment, Patient, ensure_appointment_doctor_column, ensure_appointment_expected_delivery_date_column
    
    ensure_appointment_doctor_column()
    ensure_appointment_expected_delivery_date_column()
    date_str = (request.args.get('date') or '').strip()
    if not date_str:
        return jsonify({'error': 'Thiếu tham số date'}), 400
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Định dạng ngày không hợp lệ (yyyy-mm-dd)'}), 400
    
    name = (request.args.get('name') or '').strip()
    pid = (request.args.get('pid') or '').strip()
    phone = (request.args.get('phone') or '').strip()
    status = (request.args.get('status') or '').strip()
    q = (request.args.get('q') or '').strip()

    query = (
        Appointment.query
        .join(Patient, Appointment.patient_id == Patient.id)
        .filter(db.func.date(Appointment.appointment_date) == target_date)
    )

    if status:
        query = query.filter(Appointment.status == status)
    if name:
        query = query.filter(Patient.name.ilike(f'%{name}%'))
    if phone:
        query = query.filter(Patient.phone.ilike(f'%{phone}%'))
    if pid:
        query = query.filter(Patient.patient_id.ilike(f'%{pid}%'))

    if q and not (name or pid or phone):
        q_lower = q.lower()
        q_digits = ''.join(ch for ch in q if ch.isdigit())
        conds = []
        if q_lower:
            conds.append(Patient.name.ilike(f'%{q_lower}%'))
            conds.append(Patient.phone.ilike(f'%{q_lower}%'))
        if q_digits:
            conds.append(Patient.phone.ilike(f'%{q_digits}%'))
            conds.append(Patient.patient_id.ilike(f'%{q_digits}%'))
        if conds:
            query = query.filter(or_(*conds))

    appointments = query.order_by(Appointment.appointment_date).all()
    return jsonify([_appointment_to_json(a) for a in appointments])


@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
def get_one(appointment_id):
    """GET /api/appointments/<id>"""
    from app import Appointment, _get_or_404
    
    a = _get_or_404(Appointment, appointment_id)
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
    from app import db, Appointment, MedicalRecord, _get_or_404
    
    data = request.json or {}
    diag_text = (data.get('diagnosis') or '').strip()
    appt = _get_or_404(Appointment, appointment_id)
    rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    if not rec:
        rec = MedicalRecord(patient_id=appt.patient_id, appointment_id=appointment_id)
        db.session.add(rec)
    rec.diagnosis = diag_text
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
    notes_text = (data.get('notes') or '').strip()
    appt = Appointment.query.get_or_404(appointment_id)
    rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    if not rec:
        rec = MedicalRecord(patient_id=appt.patient_id, appointment_id=appointment_id)
        db.session.add(rec)
    rec.notes = notes_text
    db.session.commit()
    return jsonify({'notes': rec.notes})
