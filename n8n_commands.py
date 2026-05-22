# -*- coding: utf-8 -*-
"""
Thực thi lệnh từ N8N (hoặc automation khác) cho Phòng khám Đại Anh.

Cấu hình: biến môi trường N8N_API_KEY (hoặc N8N_WEBHOOK_SECRET).
Header: X-N8N-API-Key: <key>  hoặc  Authorization: Bearer <key>
"""
from __future__ import annotations

import os
import re
import hmac
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from flask import request
from sqlalchemy import or_


class N8nCommandError(Exception):
  def __init__(self, message: str, code: str = 'command_error', status: int = 400, details: Any = None):
    super().__init__(message)
    self.message = message
    self.code = code
    self.status = status
    self.details = details


COMMAND_CATALOG = [
  {
    'command': 'list_today_appointments',
    'description': 'Danh sách lịch khám hôm nay',
    'params': {'q': 'optional', 'phone': 'optional', 'patient_name': 'optional', 'status': 'optional'},
  },
  {
    'command': 'list_clinical_services',
    'description': 'Danh sách dịch vụ CLS (để chọn service_id / tên)',
    'params': {'q': 'optional', 'ultrasound_only': 'optional bool'},
  },
  {
    'command': 'add_clinical_service',
    'description': 'Thêm dịch vụ CLS cho lịch khám (cần appointment_id hoặc bệnh nhân hôm nay)',
    'params': {
      'service_id': 'int hoặc',
      'service_name': 'str',
      'appointment_id': 'optional int',
      'patient_name': 'optional',
      'phone': 'optional',
      'patient_id': 'optional PID',
      'doctor_name': 'optional',
    },
  },
  {
    'command': 'add_ultrasound_12w',
    'description': 'Alias: thêm siêu âm thai ~12 tuần (tìm dịch vụ theo tên trong DB)',
    'params': 'giống add_clinical_service',
  },
]


def get_n8n_api_key() -> str:
  return (os.environ.get('N8N_API_KEY') or os.environ.get('N8N_WEBHOOK_SECRET') or '').strip()


def verify_n8n_request() -> Tuple[bool, Optional[str]]:
  expected = get_n8n_api_key()
  if not expected:
    return False, 'Chưa cấu hình N8N_API_KEY trên server'
  provided = (request.headers.get('X-N8N-API-Key') or '').strip()
  if not provided:
    auth = (request.headers.get('Authorization') or '').strip()
    if auth.lower().startswith('bearer '):
      provided = auth[7:].strip()
  if not provided or not hmac.compare_digest(provided, expected):
    return False, 'API key không hợp lệ'
  return True, None


def _norm_phone(value: str) -> str:
  return re.sub(r'\D', '', str(value or ''))


def _appointment_summary(appt) -> dict:
  p = appt.patient
  return {
    'appointment_id': appt.id,
    'appointment_date': appt.appointment_date.isoformat() if appt.appointment_date else None,
    'service_type': appt.service_type,
    'status': appt.status,
    'doctor_name': getattr(appt, 'doctor_name', None),
    'patient_id': p.patient_id if p else None,
    'patient_name': p.name if p else None,
    'patient_phone': p.phone if p else None,
  }


def _resolve_today_appointments(params: dict):
  from app import db, Appointment, Patient

  today = date.today()
  query = (
    Appointment.query.join(Patient, Appointment.patient_id == Patient.id)
    .filter(db.func.date(Appointment.appointment_date) == today)
  )
  status = (params.get('status') or '').strip()
  if status:
    query = query.filter(Appointment.status == status)

  q = (params.get('q') or '').strip()
  name = (params.get('patient_name') or params.get('name') or '').strip()
  phone = (params.get('phone') or '').strip()
  pid = (params.get('patient_id') or params.get('pid') or '').strip()

  if name:
    query = query.filter(Patient.name.ilike(f'%{name}%'))
  if phone:
    digits = _norm_phone(phone)
    if digits:
      query = query.filter(Patient.phone.ilike(f'%{digits[-9:]}%'))
  if pid:
    query = query.filter(Patient.patient_id.ilike(f'%{pid}%'))

  if q and not (name or phone or pid):
    q_lower = q.lower()
    q_digits = _norm_phone(q)
    conds = []
    if q_lower:
      conds.append(Patient.name.ilike(f'%{q_lower}%'))
      conds.append(Patient.phone.ilike(f'%{q_lower}%'))
    if q_digits:
      conds.append(Patient.phone.ilike(f'%{q_digits}%'))
      conds.append(Patient.patient_id.ilike(f'%{q_digits}%'))
    if conds:
      query = query.filter(or_(*conds))

  return query.order_by(Appointment.appointment_date).all()


def _resolve_appointment(params: dict):
  from app import Appointment

  raw_id = params.get('appointment_id')
  if raw_id is not None and str(raw_id).strip() != '':
    appt = Appointment.query.get(int(raw_id))
    if not appt:
      raise N8nCommandError(f'Không tìm thấy lịch id={raw_id}', 'not_found', 404)
    return appt

  matches = _resolve_today_appointments(params)
  if not matches:
    raise N8nCommandError(
      'Không tìm thấy lịch khám hôm nay cho bệnh nhân đã cho. Thử appointment_id hoặc phone/patient_name.',
      'not_found',
      404,
    )
  if len(matches) > 1:
    raise N8nCommandError(
      'Nhiều lịch khám trùng điều kiện hôm nay — cần appointment_id cụ thể.',
      'ambiguous',
      409,
      details=[_appointment_summary(a) for a in matches],
    )
  return matches[0]


def _resolve_clinical_service(params: dict, *, ultrasound_12w: bool = False):
  from app import ClinicalServiceSetting, db

  raw_id = params.get('service_id')
  if raw_id is not None and str(raw_id).strip() != '':
    svc = ClinicalServiceSetting.query.get(int(raw_id))
    if not svc:
      raise N8nCommandError(f'Không tìm thấy dịch vụ id={raw_id}', 'not_found', 404)
    return svc

  name = (params.get('service_name') or '').strip()
  if ultrasound_12w and not name:
    name = 'siêu âm thai 12'

  if not name:
    raise N8nCommandError('Thiếu service_id hoặc service_name', 'missing_param', 400)

  exact = ClinicalServiceSetting.query.filter(
    db.func.lower(ClinicalServiceSetting.name) == name.lower()
  ).first()
  if exact:
    return exact

  q = ClinicalServiceSetting.query.filter(ClinicalServiceSetting.name.ilike(f'%{name}%'))
  if ultrasound_12w:
    q = q.filter(
      or_(
        ClinicalServiceSetting.name.ilike('%sieu am%'),
        ClinicalServiceSetting.name.ilike('%siêu âm%'),
        ClinicalServiceSetting.service_group.ilike('%sieu am%'),
        ClinicalServiceSetting.service_group.ilike('%siêu âm%'),
      )
    ).filter(
      or_(
        ClinicalServiceSetting.name.ilike('%12%'),
        ClinicalServiceSetting.name.ilike('%12w%'),
        ClinicalServiceSetting.name.ilike('%12 tuần%'),
        ClinicalServiceSetting.name.ilike('%12 tuan%'),
      )
    )
  candidates = q.order_by(ClinicalServiceSetting.name).all()
  if not candidates:
    raise N8nCommandError(
      f'Không tìm thấy dịch vụ khớp "{name}". Gọi list_clinical_services để xem tên chính xác.',
      'not_found',
      404,
    )
  if len(candidates) > 1 and ultrasound_12w:
    # Ưu tiên tên có "12" và "thai"
    scored = []
    for c in candidates:
      n = (c.name or '').lower()
      score = 0
      if '12' in n:
        score += 2
      if 'thai' in n:
        score += 2
      if 'sieu am' in n or 'siêu âm' in n:
        score += 1
      scored.append((score, c))
    scored.sort(key=lambda x: (-x[0], x[1].name or ''))
    if scored[0][0] > 0:
      return scored[0][1]
  if len(candidates) > 1:
    raise N8nCommandError(
      f'Nhiều dịch vụ khớp "{name}" — cần service_id.',
      'ambiguous',
      409,
      details=[{'service_id': c.id, 'name': c.name, 'service_group': c.service_group} for c in candidates[:10]],
    )
  return candidates[0]


def _add_clinical_service_to_appointment(appointment_id: int, service_id: int, doctor_name: str = '') -> dict:
  """Thêm CLS — tái sử dụng logic app (lab order + MWL nếu siêu âm)."""
  from app import (
    db,
    Appointment,
    ClinicalService,
    ClinicalServiceSetting,
    LabOrder,
    ensure_clinical_service_setting_columns,
    ensure_clinical_service_sync_columns,
    ensure_lab_order_columns,
    auto_create_patient_record_entry,
    _auto_mwl_sync_after_appointment,
    _kick_Maysieuam_sync_now,
    _mwl_accession_for_appointment,
    _get_or_404,
  )

  ensure_clinical_service_setting_columns()
  ensure_clinical_service_sync_columns()
  appointment = _get_or_404(Appointment, appointment_id)
  service = _get_or_404(ClinicalServiceSetting, service_id)

  existing = ClinicalService.query.filter_by(
    appointment_id=appointment_id,
    service_id=service_id,
  ).first()
  if existing:
    return {
      'already_exists': True,
      'clinical_service_id': existing.id,
      'service_id': service_id,
      'service_name': service.name,
      'appointment_id': appointment_id,
    }

  doctor = (doctor_name or '').strip() or (getattr(appointment, 'doctor_name', '') or 'PK Đại Anh')
  clinical_service = ClinicalService(
    appointment_id=appointment_id,
    service_id=service_id,
    doctor_name=doctor,
  )
  db.session.add(clinical_service)
  db.session.flush()

  try:
    ensure_lab_order_columns()
    lab_order = LabOrder(
      test_date=appointment.appointment_date.date(),
      patient_name=appointment.patient.name,
      patient_phone=appointment.patient.phone,
      patient_dob=appointment.patient.date_of_birth.strftime('%Y-%m-%d') if appointment.patient.date_of_birth else None,
      patient_address=appointment.patient.address,
      provider_unit=service.provider_unit,
      test_type=service.name,
      price=service.price,
      status='chờ kết quả',
      appointment_id=appointment.id,
      clinical_service_id=clinical_service.id,
    )
    db.session.add(lab_order)
    db.session.flush()
    auto_create_patient_record_entry(
      appointment=appointment,
      lab_order=lab_order,
      service_name=appointment.service_type or service.name,
      note=f"Dịch vụ CLS (N8N): {service.name}",
    )
  except Exception as lab_err:
    print(f"[N8N] Lab sync failed: {lab_err}")

  is_ultrasound = False
  try:
    g = (service.service_group or '').lower()
    n = (service.name or '').lower()
    if any(x in g for x in ('siêu âm', 'sieu am', 'ultrasound')):
      is_ultrasound = True
    if any(x in n for x in ('siêu âm', 'sieu am', 'ultrasound')):
      is_ultrasound = True
    if is_ultrasound:
      appointment.Maysieuam_synced = False
      appointment.Maysieuam_sync_time = None
      clinical_service.Maysieuam_status = 'queued'
      clinical_service.Maysieuam_retry_count = 0
      clinical_service.Maysieuam_last_error = None
      clinical_service.Maysieuam_last_attempt = datetime.utcnow()
      clinical_service.Maysieuam_synced_at = None
      clinical_service.Maysieuam_accession = _mwl_accession_for_appointment(appointment_id, f"svc{service.id}")
  except Exception as e:
    print(f"[N8N] Ultrasound prep failed: {e}")

  db.session.commit()

  if is_ultrasound:
    _auto_mwl_sync_after_appointment(appointment_id)
    _kick_Maysieuam_sync_now(appointment_id, clinical_service_id=clinical_service.id)

  return {
    'already_exists': False,
    'clinical_service_id': clinical_service.id,
    'service_id': service_id,
    'service_name': service.name,
    'appointment_id': appointment_id,
    'is_ultrasound': is_ultrasound,
    'patient': _appointment_summary(appointment),
  }


def _cmd_list_today(params: dict) -> dict:
  rows = _resolve_today_appointments(params)
  items = [_appointment_summary(a) for a in rows]
  return {
    'count': len(items),
    'date': date.today().isoformat(),
    'appointments': items,
    'message': f'Có {len(items)} lịch khám hôm nay.',
  }


def _cmd_list_services(params: dict) -> dict:
  from app import ClinicalServiceSetting

  q = (params.get('q') or '').strip()
  ultrasound_only = str(params.get('ultrasound_only', '')).lower() in ('1', 'true', 'yes')
  query = ClinicalServiceSetting.query
  if q:
    query = query.filter(ClinicalServiceSetting.name.ilike(f'%{q}%'))
  rows = query.order_by(ClinicalServiceSetting.name).all()
  items = []
  for s in rows:
    g = (s.service_group or '').lower()
    n = (s.name or '').lower()
    is_us = any(x in g or x in n for x in ('siêu âm', 'sieu am', 'ultrasound'))
    if ultrasound_only and not is_us:
      continue
    items.append({
      'service_id': s.id,
      'name': s.name,
      'price': s.price,
      'service_group': s.service_group,
      'ultrasound': is_us,
    })
  return {'count': len(items), 'services': items}


def _cmd_add_clinical_service(params: dict, *, ultrasound_12w: bool = False) -> dict:
  appt = _resolve_appointment(params)
  svc = _resolve_clinical_service(params, ultrasound_12w=ultrasound_12w)
  doctor = (params.get('doctor_name') or '').strip()
  result = _add_clinical_service_to_appointment(appt.id, svc.id, doctor)
  if result.get('already_exists'):
    msg = f'Bệnh nhân đã có dịch vụ "{svc.name}" trên lịch #{appt.id}.'
  else:
    msg = f'Đã thêm "{svc.name}" cho {appt.patient.name if appt.patient else "BN"} (lịch #{appt.id}).'
    if result.get('is_ultrasound'):
      msg += ' Đã kích hoạt đồng bộ worklist siêu âm.'
  result['message'] = msg
  return result


def _parse_simple_intent(body: dict) -> Tuple[str, dict]:
  """Gợi ý: N8N có thể gửi intent + params, hoặc chỉ text."""
  text = (body.get('text') or body.get('message') or '').strip().lower()
  params = dict(body.get('params') or {})
  if body.get('patient_name') and 'patient_name' not in params:
    params['patient_name'] = body['patient_name']
  if body.get('phone') and 'phone' not in params:
    params['phone'] = body['phone']
  if body.get('appointment_id') and 'appointment_id' not in params:
    params['appointment_id'] = body['appointment_id']
  if body.get('service_name') and 'service_name' not in params:
    params['service_name'] = body['service_name']

  if not text:
    return (body.get('command') or '').strip(), params

  if any(k in text for k in ('danh sach', 'danh sách', 'list', 'khám hôm nay', 'kham hom nay', 'hôm nay')):
    if any(k in text for k in ('khám', 'kham', 'lịch', 'lich', 'appointment')):
      return 'list_today_appointments', params
  if any(k in text for k in ('thêm dịch vụ', 'them dich vu', 'add service', 'chỉ định')):
    params.setdefault('service_name', body.get('service_name') or '')
    if '12' in text and ('thai' in text or 'sieu am' in text or 'siêu âm' in text):
      return 'add_ultrasound_12w', params
    return 'add_clinical_service', params
  if '12' in text and ('sieu am' in text or 'siêu âm' in text or 'thai' in text):
    return 'add_ultrasound_12w', params
  return (body.get('command') or '').strip(), params


def execute_n8n_command(body: dict) -> dict:
  command, params = _parse_simple_intent(body or {})
  if not command:
    command = (body.get('command') or '').strip()
  if not command:
    raise N8nCommandError(
      'Thiếu command. Gọi GET /api/n8n/commands để xem danh sách.',
      'missing_command',
      400,
    )

  cmd = command.lower().replace('-', '_')
  if cmd in ('help', 'commands'):
    return {'commands': COMMAND_CATALOG}

  if cmd == 'list_today_appointments':
    data = _cmd_list_today(params)
  elif cmd == 'list_clinical_services':
    data = _cmd_list_services(params)
  elif cmd == 'add_clinical_service':
    data = _cmd_add_clinical_service(params)
  elif cmd in ('add_ultrasound_12w', 'add_ultrasound', 'add_us_12w'):
    data = _cmd_add_clinical_service(params, ultrasound_12w=True)
  else:
    raise N8nCommandError(f'Lệnh không hỗ trợ: {command}', 'unknown_command', 400)

  return {'command': cmd, 'success': True, 'data': data, 'message': data.get('message', 'OK')}
