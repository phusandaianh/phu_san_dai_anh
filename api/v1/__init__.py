# -*- coding: utf-8 -*-
"""
API v1 - Tổng hợp các module
URL: /api/login, /api/patients/..., /api/appointments/...
"""
from flask import Blueprint
from api.v1 import auth, patients, appointments

api_v1_bp = Blueprint('api_v1', __name__)

# Đăng ký sub-blueprint (url_prefix='' để giữ /api/login, /api/patients/...)
api_v1_bp.register_blueprint(auth.auth_bp, url_prefix='')
api_v1_bp.register_blueprint(patients.patients_bp, url_prefix='')
api_v1_bp.register_blueprint(appointments.appointments_bp, url_prefix='')
