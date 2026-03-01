# -*- coding: utf-8 -*-
"""
API v1 - Tổng hợp các module
URL: /api/login (trong app.py), /api/patients/..., /api/appointments/...
Không đăng ký auth blueprint - login/logout xử lý trong app.py để tránh lỗi SQLAlchemy context
"""
from flask import Blueprint
from api.v1 import patients, appointments

api_v1_bp = Blueprint('api_v1', __name__)

# Không đăng ký auth - login/logout trong app.py
api_v1_bp.register_blueprint(patients.patients_bp, url_prefix='')
api_v1_bp.register_blueprint(appointments.appointments_bp, url_prefix='')
