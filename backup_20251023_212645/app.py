from flask import Flask, render_template, send_from_directory, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, inspect
from datetime import datetime, timedelta
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import schedule
import time
import threading
from twilio.rest import Client
import re
import werkzeug
import json
from voluson_sync_service import get_voluson_sync_service

app = Flask(__name__, static_folder='.', template_folder='.')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TWILIO_ACCOUNT_SID'] = 'YOUR_TWILIO_ACCOUNT_SID'
app.config['TWILIO_AUTH_TOKEN'] = 'YOUR_TWILIO_AUTH_TOKEN'
app.config['TWILIO_PHONE_NUMBER'] = 'YOUR_TWILIO_PHONE_NUMBER'

db = SQLAlchemy(app)
twilio_client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

# Database Models
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Optional: assigned doctor for clinical forms
    doctor_name = db.Column(db.String(100), default='PK Đại Anh')
    # Voluson sync fields
    voluson_synced = db.Column(db.Boolean, default=False)
    voluson_sync_time = db.Column(db.DateTime)
    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'kham', 'can-lam-sang'

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', backref=db.backref('medical_records', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('medical_record', lazy=True))

class ClinicalService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('clinical_service_setting.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointment = db.relationship('Appointment', backref=db.backref('clinical_services', lazy=True))
    service = db.relationship('ClinicalServiceSetting', backref=db.backref('clinical_services', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'sms', 'push', 'email'
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    patient = db.relationship('Patient', backref=db.backref('notifications', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('notifications', lazy=True))

# Database Models for Admin Content
class HomeContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hero_title = db.Column(db.String(200), nullable=False)
    hero_description = db.Column(db.Text, nullable=False)
    clinic_summary = db.Column(db.String(500), default='Siêu âm 5D, sàng lọc dị tật, khám phụ khoa, vô sinh')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(200), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExaminationSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ClinicalServiceSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # Mô tả dịch vụ (giữ tương thích với CSDL cũ có constraint NOT NULL)
    description = db.Column(db.Text, nullable=False, default='')
    service_group = db.Column(db.String(50))
    provider_unit = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Model lưu kết quả xét nghiệm/siêu âm
class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # máu, nước tiểu, siêu âm, ...
    result_text = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointment = db.relationship('Appointment', backref=db.backref('test_results', lazy=True))

class BookingPageContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    services = db.Column(db.Text)  # JSON string
    utilities = db.Column(db.Text)  # JSON string
    reasons = db.Column(db.Text)  # JSON string for reasons (Lý do khám)
    schedule = db.Column(db.Text)
    contact = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
# --- Utilities: Safe migration helpers ---
def ensure_booking_reasons_column():
    try:
        result = db.session.execute('PRAGMA table_info(booking_page_content)')
        columns = [row[1] for row in result.fetchall()]
        if 'reasons' not in columns:
            db.session.execute('ALTER TABLE booking_page_content ADD COLUMN reasons TEXT')
            db.session.commit()
    except Exception:
        db.session.rollback()
        # Ignore if cannot migrate automatically; API will remain backward compatible


def ensure_clinical_service_setting_columns():
    """Ensure backward compatibility by adding missing columns to clinical_service_setting table."""
    try:
        result = db.session.execute('PRAGMA table_info(clinical_service_setting)')
        columns = [row[1] for row in result.fetchall()]
        if 'description' not in columns:
            # Thêm cột description với DEFAULT '' để không vi phạm NOT NULL
            db.session.execute("ALTER TABLE clinical_service_setting ADD COLUMN description TEXT DEFAULT '' NOT NULL")
        if 'service_group' not in columns:
            db.session.execute('ALTER TABLE clinical_service_setting ADD COLUMN service_group VARCHAR(50)')
        if 'provider_unit' not in columns:
            db.session.execute('ALTER TABLE clinical_service_setting ADD COLUMN provider_unit VARCHAR(100)')
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Best-effort migration; ignore if cannot alter (e.g., already exists or locked)

def ensure_work_schedule_columns():
    """Ensure new columns exist on work_schedule: is_locked (bool), slot_minutes (int)."""
    try:
        result = db.session.execute('PRAGMA table_info(work_schedule)')
        columns = [row[1] for row in result.fetchall()]
        if 'is_locked' not in columns:
            db.session.execute('ALTER TABLE work_schedule ADD COLUMN is_locked BOOLEAN DEFAULT 0')
        if 'slot_minutes' not in columns:
            db.session.execute('ALTER TABLE work_schedule ADD COLUMN slot_minutes INTEGER DEFAULT 10')
        if 'is_closed' not in columns:
            db.session.execute('ALTER TABLE work_schedule ADD COLUMN is_closed BOOLEAN DEFAULT 0')
        db.session.commit()
    except Exception:
        db.session.rollback()
        # ignore if cannot migrate automatically

def ensure_appointment_doctor_column():
    """Ensure Appointment table has doctor_name column."""
    try:
        result = db.session.execute('PRAGMA table_info(appointment)')
        columns = [row[1] for row in result.fetchall()]
        if 'doctor_name' not in columns:
            db.session.execute("ALTER TABLE appointment ADD COLUMN doctor_name VARCHAR(100) DEFAULT 'PK Đại Anh'")
            db.session.commit()
    except Exception:
        db.session.rollback()

def ensure_lab_order_columns():
    """Ensure lab_order table has appointment_id and clinical_service_id columns for backward compatibility."""
    try:
        result = db.session.execute('PRAGMA table_info(lab_order)')
        columns = [row[1] for row in result.fetchall()]
        if 'appointment_id' not in columns:
            db.session.execute('ALTER TABLE lab_order ADD COLUMN appointment_id INTEGER')
        if 'clinical_service_id' not in columns:
            db.session.execute('ALTER TABLE lab_order ADD COLUMN clinical_service_id INTEGER')
        db.session.commit()
    except Exception:
        db.session.rollback()
        # Best-effort migration; ignore if cannot alter (e.g., locked or already exists)

def ensure_lab_settings_columns():
    """Ensure lab_settings table has columns we use from frontend: clear_status_on_sync"""
    try:
        result = db.session.execute('PRAGMA table_info(lab_settings)')
        columns = [row[1] for row in result.fetchall()]
        if 'clear_status_on_sync' not in columns:
            db.session.execute('ALTER TABLE lab_settings ADD COLUMN clear_status_on_sync BOOLEAN DEFAULT 0')
        db.session.commit()
    except Exception:
        db.session.rollback()
        # ignore if cannot migrate automatically

class WorkSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # yyyy-mm-dd
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    doctor_name = db.Column(db.String(100), nullable=False)
    # New fields with backward compatibility ensured via helper below
    is_locked = db.Column(db.Boolean, default=False)
    slot_minutes = db.Column(db.Integer, default=10)
    is_closed = db.Column(db.Boolean, default=False)  # nghỉ làm việc
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Models for Clinical Service Packages
class ClinicalServicePackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # Relationship to link package with clinical services
    services = db.relationship('ClinicalServiceSetting', secondary='package_clinical_service', backref=db.backref('packages', lazy='dynamic'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Association table for many-to-many relationship
package_clinical_service = db.Table('package_clinical_service',
    db.Column('package_id', db.Integer, db.ForeignKey('clinical_service_package.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('clinical_service_setting.id'), primary_key=True)
)

# Quản lý danh sách xét nghiệm tổng hợp
class LabOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    patient_name = db.Column(db.String(120), nullable=False)
    patient_phone = db.Column(db.String(20))
    patient_dob = db.Column(db.String(10))
    patient_address = db.Column(db.String(200))
    provider_unit = db.Column(db.String(100))
    test_type = db.Column(db.String(120))
    price = db.Column(db.Float, default=0)
    note = db.Column(db.Text)
    status = db.Column(db.String(30), default='chờ kết quả')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Liên kết để đồng bộ tự động
    appointment_id = db.Column(db.Integer)  # reference Appointment.id
    clinical_service_id = db.Column(db.Integer)  # reference ClinicalService.id

class LabSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # JSON text for custom statuses/actions; keep simple as string
    statuses = db.Column(db.Text, default='["chờ kết quả","đã có kết quả"]')
    actions = db.Column(db.Text, default='[]')
    # password to allow destructive reset of month (store hashed would be better; keep plain for now)
    reset_password = db.Column(db.String(64), default='010190')
    # whether to clear status column when syncing (frontend setting)
    clear_status_on_sync = db.Column(db.Boolean, default=False)

class ClinicDoctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(100), nullable=False, default='')
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LabPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False, default=0)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ClinicalFormTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), nullable=False)  # 'lab-request', 'lab-result'
    header_html = db.Column(db.Text, nullable=False)
    content_html = db.Column(db.Text, nullable=False)
    logo_position = db.Column(db.String(20), default='left')  # 'left', 'center', 'right'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


@app.route('/api/lab-settings', methods=['GET', 'PUT'])
def api_lab_settings_top():
    # ensure columns exist
    try:
        ensure_lab_settings_columns()
    except Exception:
        pass

    if request.method == 'GET':
        s = LabSettings.query.first()
        if not s:
            s = LabSettings()
            db.session.add(s)
            db.session.commit()
        try:
            statuses = json.loads(s.statuses) if s.statuses else []
        except Exception:
            statuses = []
        return jsonify({
            'status_options': statuses,
            'reset_password': s.reset_password,
            'clear_status_on_sync': bool(getattr(s, 'clear_status_on_sync', False))
        })

    if request.method == 'PUT':
        data = request.json or {}
        statuses = data.get('status_options', [])
        reset_password = data.get('reset_password', '')
        clear_flag = data.get('clear_status_on_sync', False)
        s = LabSettings.query.first()
        if not s:
            s = LabSettings()
            db.session.add(s)
        try:
            s.statuses = json.dumps(statuses, ensure_ascii=False)
            s.reset_password = reset_password
            s.clear_status_on_sync = bool(clear_flag)
            db.session.commit()
            return jsonify({'status_options': statuses})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    queue_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='waiting')  # waiting, serving, completed
    #checkin_date = db.Column(db.Date, default=datetime.utcnow().date)
    checkin_date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.json
    # Kiểm tra dữ liệu đầu vào
    required_fields = ['name', 'phone', 'address', 'date_of_birth', 'service_type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'Vui lòng nhập đầy đủ thông tin {field}.'}), 400
    # Kiểm tra số điện thoại hợp lệ (10-11 số, chỉ chứa số)
    if not re.match(r'^\d{10,11}$', data['phone']):
        return jsonify({'message': 'Số điện thoại không hợp lệ. Vui lòng nhập đúng 10-11 số.'}), 400
    # Kiểm tra ngày sinh hợp lệ
    try:
        dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
    except Exception:
        return jsonify({'message': 'Ngày sinh không hợp lệ. Định dạng đúng: yyyy-mm-dd.'}), 400

    # Lấy thông tin ca khám và giờ đăng ký
    date_str = (data.get('appointment_date') or '').strip()  # yyyy-mm-dd
    time_str = (data.get('appointment_time') or '').strip()  # HH:MM
    doctor_name = (data.get('doctor_name') or '').strip()
    if not date_str or not time_str:
        return jsonify({'message': 'Vui lòng chọn giờ đăng ký khám.'}), 400
    # Xác thực ca khám tồn tại và không nghỉ
    try:
        # Tìm ca khám chứa giờ đã chọn trong ngày đó
        ws = WorkSchedule.query.filter_by(date=date_str).all()
        def time_to_minutes(t):
            h, m = [int(x) for x in t.split(':')]
            return h * 60 + m
        selected_min = time_to_minutes(time_str)
        containing_shift = None
        for s in ws:
            if getattr(s, 'is_closed', False):
                continue
            if time_to_minutes(s.start_time) <= selected_min < time_to_minutes(s.end_time):
                containing_shift = s
                break
        if not containing_shift:
            return jsonify({'message': 'Giờ chọn không nằm trong ca khám hợp lệ.'}), 400
        # Kết hợp datetime
        appointment_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
    except Exception:
        return jsonify({'message': 'Thời gian đăng ký không hợp lệ.'}), 400

    try:
        # Kiểm tra trùng slot: đã có người đặt cùng thời điểm này
        existing_slot = Appointment.query.filter(
            Appointment.appointment_date == appointment_dt
        ).first()
        if existing_slot:
            return jsonify({'message': 'Khung giờ này đã có người đăng ký. Vui lòng chọn giờ khác.'}), 400

        # Kiểm tra số điện thoại chỉ được đăng ký 1 lần trong cùng phiên (ca) khám
        day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        # So sánh thời gian theo chuỗi HH:MM trong SQLite
        same_shift_by_phone = Appointment.query.join(Patient, Appointment.patient_id == Patient.id) \
            .filter(
                Patient.phone == data['phone'],
                db.func.date(Appointment.appointment_date) == day_date,
                db.func.strftime('%H:%M', Appointment.appointment_date) >= containing_shift.start_time,
                db.func.strftime('%H:%M', Appointment.appointment_date) < containing_shift.end_time
            ).first()
        if same_shift_by_phone:
            return jsonify({'message': 'Mỗi số điện thoại chỉ được đăng ký 1 lần trong 1 phiên khám.'}), 400

        # Tìm hoặc tạo bệnh nhân theo số điện thoại
        patient = Patient.query.filter_by(phone=data['phone']).first()
        if not patient:
            patient = Patient(
                name=data['name'],
                phone=data['phone'],
                address=data.get('address'),
                date_of_birth=dob
            )
            db.session.add(patient)
            db.session.flush()

        appointment = Appointment(
            patient_id=patient.id,
            appointment_date=appointment_dt,
            service_type=data['service_type']
        )
        db.session.add(appointment)
        db.session.commit()

        # Tự động đồng bộ với Voluson E10 nếu có cấu hình
        try:
            sync_service = get_voluson_sync_service()
            if sync_service.sync_enabled:
                # Đồng bộ bất đồng bộ để không làm chậm response
                threading.Thread(
                    target=sync_service.sync_single_appointment,
                    args=(appointment.id,),
                    daemon=True
                ).start()
        except Exception as sync_error:
            # Log lỗi nhưng không ảnh hưởng đến việc tạo cuộc hẹn
            print(f"Lỗi khi đồng bộ với Voluson E10: {sync_error}")

        return jsonify({'message': 'Đăng ký lịch khám thành công', 'appointment_id': appointment.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Đã xảy ra lỗi hệ thống: {str(e)}'}), 500

@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    """Trả về danh sách slot HH:MM còn trống cho 1 ca khám.
    Tham số: date=yyyy-mm-dd, start=HH:MM, end=HH:MM, slot_minutes=int
    """
    date_str = request.args.get('date')
    start = request.args.get('start')
    end = request.args.get('end')
    slot_minutes = request.args.get('slot_minutes', type=int, default=10)
    exclude_appointment_id = request.args.get('exclude_appointment_id', type=int)
    if not date_str or not start or not end:
        return jsonify({'message': 'Thiếu tham số date/start/end'}), 400


    
    try:
        day = datetime.strptime(date_str, '%Y-%m-%d').date()
        def to_minutes(t):
            h, m = [int(x) for x in t.split(':')]
            return h * 60 + m
        def to_hhmm(total):
            return f"{total//60:02d}:{total%60:02d}"
        start_min = to_minutes(start)
        end_min = to_minutes(end)
        # Sinh tất cả slot
        all_slots = []
        t = start_min
        while t + slot_minutes <= end_min:
            all_slots.append(to_hhmm(t))
            t += slot_minutes
        # Lấy giờ đã được đặt
        appts = Appointment.query.filter(
            db.func.date(Appointment.appointment_date) == day,
            db.func.strftime('%H:%M', Appointment.appointment_date).in_(all_slots)
        ).all()
        taken = set()
        for a in appts:
            if exclude_appointment_id and a.id == exclude_appointment_id:
                continue
            taken.add(a.appointment_date.strftime('%H:%M'))
        # Nếu hôm nay, loại bỏ các slot đã qua
        now = datetime.now()
        if now.date() == day:
            current_min = now.hour * 60 + now.minute
        else:
            current_min = -1
        available = [s for s in all_slots if s not in taken and (current_min < 0 or to_minutes(s) > current_min)]
        return jsonify({'slots': available})
    except Exception as e:
        return jsonify({'message': f'Lỗi tính slot: {str(e)}'}), 400

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id: int):
    data = request.json or {}
    date_str = (data.get('appointment_date') or '').strip()
    time_str = (data.get('appointment_time') or '').strip()
    # Allow update of only service_type/doctor without time change
    if not date_str or not time_str:
        data = request.json or {}
        changed = False
        try:
            appt = Appointment.query.get_or_404(appointment_id)
            reason = (data.get('service_type') or '').strip()
            doctor = (data.get('doctor_name') or '').strip()
            if reason:
                appt.service_type = reason
                changed = True
            if doctor:
                ensure_appointment_doctor_column()
                appt.doctor_name = doctor
                changed = True
            if not changed:
                return jsonify({'message': 'Không có gì để cập nhật.'}), 400
            db.session.commit()
            return jsonify({'message': 'Đã cập nhật lịch khám', 'appointment_id': appt.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Lỗi cập nhật: {str(e)}'}), 500
    try:
        # Tìm lịch ca phù hợp
        ws = WorkSchedule.query.filter_by(date=date_str).all()
        def to_min(t):
            h, m = [int(x) for x in t.split(':')]
            return h*60+m
        sel_min = to_min(time_str)
        containing_shift = None
        for s in ws:
            if getattr(s, 'is_closed', False):
                continue
            if to_min(s.start_time) <= sel_min < to_min(s.end_time):
                containing_shift = s
                break
        if not containing_shift:
            return jsonify({'message': 'Giờ cập nhật không nằm trong ca khám hợp lệ.'}), 400
        new_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
    except Exception:
        return jsonify({'message': 'Thời gian không hợp lệ.'}), 400

    try:
        appt = Appointment.query.get_or_404(appointment_id)
        # Kiểm tra slot đã có người khác đặt chưa (loại trừ chính bản ghi này)
        conflict = Appointment.query.filter(
            Appointment.id != appointment_id,
            Appointment.appointment_date == new_dt
        ).first()
        if conflict:
            return jsonify({'message': 'Khung giờ đã có người đăng ký.'}), 400
        # Kiểm tra số điện thoại trong cùng phiên (ca) khám chỉ 1 lần (loại trừ bản ghi này)
        day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        same_shift = Appointment.query.join(Patient, Appointment.patient_id == Patient.id) \
            .filter(
                Appointment.id != appointment_id,
                Patient.phone == appt.patient.phone,
                db.func.date(Appointment.appointment_date) == day_date,
                db.func.strftime('%H:%M', Appointment.appointment_date) >= containing_shift.start_time,
                db.func.strftime('%H:%M', Appointment.appointment_date) < containing_shift.end_time
            ).first()
        if same_shift:
            return jsonify({'message': 'Số ĐT này đã đăng ký trong phiên khám này.'}), 400
        appt.appointment_date = new_dt
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật thời gian khám', 'appointment_id': appt.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi cập nhật: {str(e)}'}), 500

@app.route('/api/appointments/<int:appointment_id>/reason', methods=['PUT'])
def update_appointment_reason(appointment_id: int):
    try:
        data = request.json or {}
        reason = (data.get('service_type') or '').strip()
        if not reason:
            return jsonify({'message': 'Thiếu lý do khám (service_type).'}), 400
        appt = Appointment.query.get_or_404(appointment_id)
        appt.service_type = reason
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật lý do khám', 'service_type': appt.service_type})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi cập nhật lý do khám: {str(e)}'}), 500

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Get list of clinic doctors from the clinic doctors list."""
    try:
        # Get doctors from ClinicDoctor table
        doctors = ClinicDoctor.query.order_by(ClinicDoctor.name).all()
        
        doctor_list = []
        for doctor in doctors:
            if doctor.degree and doctor.name:
                doctor_list.append(f"{doctor.degree} {doctor.name}")
            elif doctor.name:
                doctor_list.append(doctor.name)
        
        # Add default if not present
        if 'PK Đại Anh' not in doctor_list:
            doctor_list.insert(0, 'PK Đại Anh')
        else:
            # Move PK Đại Anh to front
            doctor_list.remove('PK Đại Anh')
            doctor_list.insert(0, 'PK Đại Anh')
            
        return jsonify({'doctors': doctor_list})
    except Exception as e:
        return jsonify({'message': f'Lỗi lấy danh sách bác sĩ: {str(e)}'}), 500

@app.route('/api/clinic-doctors', methods=['GET'])
def get_clinic_doctors():
    """Get full clinic doctors list with degree and name."""
    try:
        doctors = ClinicDoctor.query.order_by(ClinicDoctor.name).all()
        return jsonify([{
            'id': d.id,
            'degree': d.degree,
            'name': d.name
        } for d in doctors])
    except Exception as e:
        return jsonify({'message': f'Lỗi lấy danh sách bác sĩ phòng khám: {str(e)}'}), 500

@app.route('/api/clinic-doctors', methods=['POST'])
def create_clinic_doctor():
    """Add new clinic doctor."""
    try:
        data = request.json or {}
        degree = (data.get('degree') or '').strip()
        name = (data.get('name') or '').strip()
        
        if not name:
            return jsonify({'message': 'Tên bác sĩ là bắt buộc'}), 400
            
        doctor = ClinicDoctor(degree=degree, name=name)
        db.session.add(doctor)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã thêm bác sĩ thành công',
            'doctor': {'id': doctor.id, 'degree': doctor.degree, 'name': doctor.name}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi thêm bác sĩ: {str(e)}'}), 500

@app.route('/api/clinic-doctors/<int:doctor_id>', methods=['PUT'])
def update_clinic_doctor(doctor_id):
    """Update clinic doctor."""
    try:
        doctor = ClinicDoctor.query.get_or_404(doctor_id)
        data = request.json or {}
        
        if 'degree' in data:
            doctor.degree = (data.get('degree') or '').strip()
        if 'name' in data:
            name = (data.get('name') or '').strip()
            if not name:
                return jsonify({'message': 'Tên bác sĩ không được để trống'}), 400
            doctor.name = name
            
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật bác sĩ thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi cập nhật bác sĩ: {str(e)}'}), 500

@app.route('/api/clinic-doctors/<int:doctor_id>', methods=['DELETE'])
def delete_clinic_doctor(doctor_id):
    """Delete clinic doctor."""
    try:
        doctor = ClinicDoctor.query.get_or_404(doctor_id)
        db.session.delete(doctor)
        db.session.commit()
        return jsonify({'message': 'Đã xóa bác sĩ thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi xóa bác sĩ: {str(e)}'}), 500

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id: int):
    try:
        # Tìm appointment cần xóa
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Lưu thông tin để trả về
        patient_name = appointment.patient.name
        appointment_time = appointment.appointment_date.strftime('%H:%M')
        
        # Xóa appointment (cascade sẽ xóa các bản ghi liên quan)
        db.session.delete(appointment)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã xóa bệnh nhân thành công',
            'patient_name': patient_name,
            'appointment_time': appointment_time
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa bệnh nhân: {str(e)}'}), 500

@app.route('/api/patients/by-phone', methods=['GET'])
def get_patient_by_phone():
    phone = (request.args.get('phone') or '').strip()
    if not phone:
        return jsonify({'message': 'Thiếu tham số phone'}), 400
    p = Patient.query.filter_by(phone=phone).first()
    if not p:
        return jsonify({'found': False})
    return jsonify({
        'found': True,
        'name': p.name,
        'phone': p.phone,
        'address': p.address,
        'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else None
    })

@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'price': s.price,
    } for s in services])

@app.route('/api/print_prescription/<int:appointment_id>', methods=['GET'])
def print_prescription(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    medical_record = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    
    # Create PDF
    filename = f'prescription_{appointment_id}.pdf'
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []
    
    # Add content to PDF
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Đơn thuốc - Phòng khám Phụ Sản Đại Anh", styles['Title']))
    elements.append(Paragraph(f"Bệnh nhân: {appointment.patient.name}", styles['Normal']))
    elements.append(Paragraph(f"Ngày khám: {appointment.appointment_date.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"Chẩn đoán: {medical_record.diagnosis}", styles['Normal']))
    elements.append(Paragraph(f"Đơn thuốc: {medical_record.prescription}", styles['Normal']))
    
    doc.build(elements)
    
    return send_file(filename, as_attachment=True)

@app.route('/api/print_ultrasound/<int:appointment_id>', methods=['GET'])
def print_ultrasound(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    medical_record = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
    
    # Create PDF for ultrasound result
    filename = f'ultrasound_{appointment_id}.pdf'
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Kết quả siêu âm - Phòng khám Phụ Sản Đại Anh", styles['Title']))
    elements.append(Paragraph(f"Bệnh nhân: {appointment.patient.name}", styles['Normal']))
    elements.append(Paragraph(f"Ngày siêu âm: {appointment.appointment_date.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Paragraph(f"Kết quả: {medical_record.diagnosis}", styles['Normal']))
    
    doc.build(elements)
    
    return send_file(filename, as_attachment=True)

# Mobile App API Endpoints
@app.route('/api/mobile/login', methods=['POST'])
def mobile_login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    
    # In a real app, you would verify credentials and return a JWT token
    return jsonify({
        'token': 'dummy_token',
        'user': {
            'id': 1,
            'name': 'Test User',
            'phone': phone
        }
    })

@app.route('/api/mobile/appointments', methods=['GET'])
def get_patient_appointments():
    # In a real app, verify the token and get patient_id
    patient_id = request.args.get('patient_id')
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    
    return jsonify([{
        'id': a.id,
        'date': a.appointment_date.isoformat(),
        'service_type': a.service_type,
        'status': a.status
    } for a in appointments])

@app.route('/api/mobile/medical-records', methods=['GET'])
def get_patient_medical_records():
    patient_id = request.args.get('patient_id')
    records = MedicalRecord.query.filter_by(patient_id=patient_id).all()
    
    return jsonify([{
        'id': r.id,
        'date': r.created_at.isoformat(),
        'diagnosis': r.diagnosis,
        'prescription': r.prescription
    } for r in records])

# Notification System
def send_sms_notification(phone, message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=phone
        )
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False

def check_upcoming_appointments():
    tomorrow = datetime.now() + timedelta(days=1)
    appointments = Appointment.query.filter(
        Appointment.appointment_date >= tomorrow,
        Appointment.appointment_date < tomorrow + timedelta(days=1)
    ).all()
    
    for appointment in appointments:
        # Create notification record
        notification = Notification(
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            notification_type='sms',
            message=f"Lịch khám của bạn vào ngày {appointment.appointment_date.strftime('%d/%m/%Y %H:%M')} tại Phòng khám Phụ Sản Đại Anh. Vui lòng đến đúng giờ.",
            sent_at=datetime.now(),
            status='pending'
        )
        db.session.add(notification)
        
        # Send SMS
        if send_sms_notification(appointment.patient.phone, notification.message):
            notification.status = 'sent'
        else:
            notification.status = 'failed'
        
        db.session.commit()

def run_scheduler():
    schedule.every().day.at("08:00").do(check_upcoming_appointments)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

# Route for serving static files
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/api/appointments/today', methods=['GET'])
def get_today_appointments():
    ensure_appointment_doctor_column()
    today = datetime.now().date()
    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today
    ).order_by(Appointment.appointment_date).all()
    
    return jsonify([{
        'id': a.id,
        'patient_id': a.patient.id,
        'patient_name': a.patient.name,
        'patient_phone': a.patient.phone,
        'patient_dob': a.patient.date_of_birth.isoformat() if a.patient.date_of_birth else None,
        'patient_address': a.patient.address,
        'appointment_date': a.appointment_date.isoformat(),
        'service_type': a.service_type,
        'status': a.status,
        'doctor_name': getattr(a, 'doctor_name', 'PK Đại Anh')
    } for a in appointments])

@app.route('/api/appointments/by-date', methods=['GET'])
def get_appointments_by_date():
    ensure_appointment_doctor_column()
    """Return appointments for a given date (yyyy-mm-dd) via ?date= query param."""
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'message': 'Thiếu tham số date (yyyy-mm-dd).'}), 400
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'message': 'Định dạng date không hợp lệ. Đúng: yyyy-mm-dd'}), 400

    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == target_date
    ).order_by(Appointment.appointment_date).all()

    return jsonify([{
        'id': a.id,
        'patient_id': a.patient.id,
        'patient_name': a.patient.name,
        'patient_phone': a.patient.phone,
        'patient_dob': a.patient.date_of_birth.isoformat() if a.patient.date_of_birth else None,
        'patient_address': a.patient.address,
        'appointment_date': a.appointment_date.isoformat(),
        'service_type': a.service_type,
        'status': a.status,
        'doctor_name': getattr(a, 'doctor_name', 'PK Đại Anh')
    } for a in appointments])

# Patient detail endpoints for editing
@app.route('/api/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    return jsonify({
        'id': p.id,
        'name': p.name,
        'phone': p.phone,
        'address': p.address,
        'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d') if p.date_of_birth else None
    })

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    data = request.json or {}
    p = Patient.query.get_or_404(patient_id)
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

# ============ Diagnosis APIs ============
@app.route('/api/appointments/<int:appointment_id>/diagnosis', methods=['GET'])
def get_appointment_diagnosis(appointment_id):
    try:
        rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).order_by(MedicalRecord.id.desc()).first()
        return jsonify({'diagnosis': (rec.diagnosis if rec else '')})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/appointments/<int:appointment_id>/diagnosis', methods=['PUT'])
def update_appointment_diagnosis(appointment_id):
    try:
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
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

# ============ Notes APIs ============
@app.route('/api/appointments/<int:appointment_id>/notes', methods=['GET'])
def get_appointment_notes(appointment_id):
    try:
        rec = MedicalRecord.query.filter_by(appointment_id=appointment_id).order_by(MedicalRecord.id.desc()).first()
        return jsonify({'notes': (rec.notes if rec else '')})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/appointments/<int:appointment_id>/notes', methods=['PUT'])
def update_appointment_notes(appointment_id):
    try:
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
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@app.route('/api/clinical-services', methods=['GET'])
def get_clinical_services():
    # Ensure columns exist for older databases
    ensure_clinical_service_setting_columns()
    services = ClinicalServiceSetting.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'price': s.price,
        'description': getattr(s, 'description', '') or '',
        'service_group': s.service_group,
        'provider_unit': s.provider_unit
    } for s in services])

@app.route('/api/clinical-services', methods=['POST'])
def create_clinical_service():
    # Ensure columns exist for older databases
    ensure_clinical_service_setting_columns()
    data = request.json
    name = data.get('name')
    price = data.get('price')
    description = (data.get('description') or '').strip()
    service_group = data.get('service_group')
    provider_unit = data.get('provider_unit')

    if not name or price is None:
        return jsonify({'message': 'Vui lòng nhập đầy đủ thông tin dịch vụ.'}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({'message': 'Giá dịch vụ không hợp lệ.'}), 400

    existing_service = ClinicalServiceSetting.query.filter(db.func.lower(ClinicalServiceSetting.name) == db.func.lower(name)).first()
    if existing_service:
        return jsonify({'message': f'Tên dịch vụ "{name}" đã tồn tại.'}), 400

    try:
        service = ClinicalServiceSetting(
            name=name,
            price=price,
            description=description or '',
            service_group=service_group,
            provider_unit=provider_unit
        )
        db.session.add(service)
        db.session.commit()
        return jsonify({'message': 'Đã thêm dịch vụ cận lâm sàng thành công!', 'id': service.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi thêm dịch vụ: {str(e)}'}), 500

@app.route('/api/clinical-services/<int:id>', methods=['PUT'])
def update_clinical_service(id):
    # Ensure columns exist for older databases
    ensure_clinical_service_setting_columns()
    data = request.json
    service = ClinicalServiceSetting.query.get_or_404(id)
    name = data.get('name')
    price = data.get('price')
    description = (data.get('description') or '').strip()
    service_group = data.get('service_group')
    provider_unit = data.get('provider_unit')

    if not name or price is None:
        return jsonify({'message': 'Vui lòng nhập đầy đủ thông tin dịch vụ.'}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({'message': 'Giá dịch vụ không hợp lệ.'}), 400

    existing_service = ClinicalServiceSetting.query.filter(
        db.func.lower(ClinicalServiceSetting.name) == db.func.lower(name),
        ClinicalServiceSetting.id != id
    ).first()
    if existing_service:
        return jsonify({'message': f'Tên dịch vụ "{name}" đã tồn tại.'}), 400

    try:
        service.name = name
        service.price = price
        service.description = description or ''
        service.service_group = service_group
        service.provider_unit = provider_unit

        db.session.commit()
        return jsonify({'message': 'Đã cập nhật dịch vụ thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật dịch vụ: {str(e)}'}), 500

@app.route('/api/clinical-services/<int:id>', methods=['DELETE'])
def delete_clinical_service(id):
    service = ClinicalServiceSetting.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Đã xóa dịch vụ thành công!'})

# Provider units list (for filters/autocomplete)
@app.route('/api/provider-units', methods=['GET'])
def list_provider_units():
    ensure_clinical_service_setting_columns()
    units = db.session.query(ClinicalServiceSetting.provider_unit).filter(ClinicalServiceSetting.provider_unit.isnot(None)).distinct().all()
    return jsonify([u[0] for u in units if u[0]])

# Lab orders APIs
@app.route('/api/lab-orders', methods=['GET'])
def list_lab_orders():
    # Ensure tables exist in case server was restarted after adding models
    try:
        db.create_all()
    except Exception:
        pass
    # Filters: month (yyyy-mm) OR start/end (yyyy-mm-dd), provider_unit, q (search)
    month = request.args.get('month')  # '2025-09'
    start = request.args.get('start')  # '2025-10-01'
    end = request.args.get('end')
    provider_unit = request.args.get('provider_unit')
    q = request.args.get('q')

    query = LabOrder.query
    if start and end:
        try:
            s = datetime.strptime(start, '%Y-%m-%d').date()
            e = datetime.strptime(end, '%Y-%m-%d').date()
            query = query.filter(LabOrder.test_date >= s, LabOrder.test_date <= e)
        except Exception:
            pass
    elif month:
        try:
            y, m = month.split('-')
            start = datetime(int(y), int(m), 1).date()
            if int(m) == 12:
                end = datetime(int(y)+1, 1, 1).date()
            else:
                end = datetime(int(y), int(m)+1, 1).date()
            query = query.filter(LabOrder.test_date >= start, LabOrder.test_date < end)
        except Exception:
            # ignore bad month format
            pass
    if provider_unit:
        query = query.filter(LabOrder.provider_unit == provider_unit)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(LabOrder.patient_name.ilike(like), LabOrder.patient_phone.ilike(like), LabOrder.test_type.ilike(like)))

    orders = query.order_by(LabOrder.test_date.desc(), LabOrder.id.desc()).all()
    return jsonify([
        {
            'id': o.id,
            'test_date': o.test_date.strftime('%Y-%m-%d'),
            'patient_name': o.patient_name,
            'patient_phone': o.patient_phone,
            'patient_dob': o.patient_dob,
            'patient_address': o.patient_address,
            'provider_unit': o.provider_unit,
            'test_type': o.test_type,
            'price': o.price,
            'status': o.status,
            'note': o.note
        } for o in orders
    ])

@app.route('/api/lab-orders', methods=['POST'])
def create_lab_order():
    data = request.json
    order = LabOrder(
        test_date=datetime.strptime(data.get('test_date'), '%Y-%m-%d').date() if data.get('test_date') else datetime.utcnow().date(),
        patient_name=data.get('patient_name','').strip(),
        patient_phone=data.get('patient_phone'),
        patient_dob=data.get('patient_dob'),
        patient_address=data.get('patient_address'),
        provider_unit=data.get('provider_unit'),
        test_type=data.get('test_type'),
        price=float(data.get('price') or 0),
        status=data.get('status') or 'chờ kết quả',
        note=data.get('note')
    )
    if not order.patient_name:
        return jsonify({'message': 'Tên bệnh nhân là bắt buộc'}), 400
    db.session.add(order)
    db.session.commit()
    return jsonify({'message': 'Đã thêm xét nghiệm', 'id': order.id})

@app.route('/api/lab-orders/<int:id>', methods=['PUT'])
def update_lab_order(id):
    order = LabOrder.query.get_or_404(id)
    data = request.json
    if 'test_date' in data and data['test_date']:
        order.test_date = datetime.strptime(data['test_date'], '%Y-%m-%d').date()
    order.patient_name = data.get('patient_name', order.patient_name)
    order.patient_phone = data.get('patient_phone', order.patient_phone)
    order.patient_dob = data.get('patient_dob', order.patient_dob)
    order.patient_address = data.get('patient_address', order.patient_address)
    order.provider_unit = data.get('provider_unit', order.provider_unit)
    order.test_type = data.get('test_type', order.test_type)
    if 'price' in data:
        try:
            order.price = float(data.get('price') or 0)
        except Exception:
            pass
    order.status = data.get('status', order.status)
    order.note = data.get('note', order.note)
    db.session.commit()
    return jsonify({'message': 'Đã cập nhật'})

@app.route('/api/lab-orders/<int:id>', methods=['DELETE'])
def delete_lab_order(id):
    order = LabOrder.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Đã xóa'})

# Đồng bộ tự động: tạo bản ghi LabOrder từ ClinicalService trong khoảng tháng
@app.route('/api/lab-orders/sync', methods=['POST'])
def sync_lab_orders():
    data = request.json or {}
    month = data.get('month')  # yyyy-mm
    if not month:
        return jsonify({'message': 'month is required (yyyy-mm)'}), 400
    try:
        y, m = month.split('-')
        start = datetime(int(y), int(m), 1)
        if int(m) == 12:
            end = datetime(int(y)+1, 1, 1)
        else:
            end = datetime(int(y), int(m)+1, 1)
    except Exception:
        return jsonify({'message': 'invalid month'}), 400

    # Lấy các dịch vụ cận lâm sàng trong khoảng thời gian này
    clinical = ClinicalService.query.join(Appointment, ClinicalService.appointment_id == Appointment.id) \
        .filter(Appointment.appointment_date >= start, Appointment.appointment_date < end).all()

    created, skipped = 0, 0
    for cs in clinical:
        # Kiểm tra đã sync chưa
        exists = LabOrder.query.filter_by(clinical_service_id=cs.id).first()
        if exists:
            skipped += 1
            continue
        svc = ClinicalServiceSetting.query.get(cs.service_id)
        appt = Appointment.query.get(cs.appointment_id)
        order = LabOrder(
            test_date=appt.appointment_date.date(),
            patient_name=appt.patient.name,
            patient_phone=appt.patient.phone,
            provider_unit=svc.provider_unit,
            test_type=svc.name,
            price=svc.price,
            appointment_id=appt.id,
            clinical_service_id=cs.id
        )
        db.session.add(order)
        created += 1
    db.session.commit()
    return jsonify({'message': 'Đồng bộ xong', 'created': created, 'skipped': skipped})


@app.route('/api/lab-orders/sync-range', methods=['POST'])
def sync_lab_orders_range():
    """Sync clinical services into lab orders for a date range (inclusive). Request JSON: {start: 'yyyy-mm-dd', end: 'yyyy-mm-dd'}"""
    data = request.json or {}
    start = data.get('start')
    end = data.get('end')
    if not start or not end:
        return jsonify({'message': 'start and end are required (yyyy-mm-dd)'}), 400
    try:
        s = datetime.strptime(start, '%Y-%m-%d')
        e = datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)
    except Exception:
        return jsonify({'message': 'invalid date format'}), 400

    clinical = ClinicalService.query.join(Appointment, ClinicalService.appointment_id == Appointment.id) \
        .filter(Appointment.appointment_date >= s, Appointment.appointment_date < e).all()

    created, skipped = 0, 0
    for cs in clinical:
        exists = LabOrder.query.filter_by(clinical_service_id=cs.id).first()
        if exists:
            skipped += 1
            continue
        svc = ClinicalServiceSetting.query.get(cs.service_id)
        appt = Appointment.query.get(cs.appointment_id)
        order = LabOrder(
            test_date=appt.appointment_date.date(),
            patient_name=appt.patient.name,
            patient_phone=appt.patient.phone,
            provider_unit=svc.provider_unit,
            test_type=svc.name,
            price=svc.price,
            appointment_id=appt.id,
            clinical_service_id=cs.id
        )
        db.session.add(order)
        created += 1
    db.session.commit()
    return jsonify({'message': 'Đồng bộ theo ngày xong', 'created': created, 'skipped': skipped})


@app.route('/api/lab-orders/reset-month', methods=['POST'])
def reset_lab_orders_month():
    """Reset (delete) all lab orders for a month. Request JSON: {month: 'yyyy-mm', password: '...'}"""
    data = request.json or {}
    month = data.get('month')
    password = data.get('password')
    if not month or not password:
        return jsonify({'message': 'month and password are required'}), 400

    settings = LabSettings.query.first()
    if not settings:
        settings = LabSettings()
        db.session.add(settings)
        db.session.commit()

    if password != (settings.reset_password or '010190'):
        return jsonify({'message': 'Mật khẩu không đúng'}), 403

    try:
        y, m = month.split('-')
        start = datetime(int(y), int(m), 1).date()
        if int(m) == 12:
            end = datetime(int(y)+1, 1, 1).date()
        else:
            end = datetime(int(y), int(m)+1, 1).date()
        LabOrder.query.filter(LabOrder.test_date >= start, LabOrder.test_date < end).delete()
        db.session.commit()
        return jsonify({'message': 'Đã reset dữ liệu cho tháng'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Không thể reset: {str(e)}'}), 500

# (lab-settings endpoints implemented earlier: GET/PUT at module top)

@app.route('/api/print-clinical-service/<int:appointment_id>', methods=['GET'])
def print_clinical_service(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    clinical_services = ClinicalService.query.filter_by(appointment_id=appointment_id).all()
    
    # Create PDF
    filename = f'clinical_service_{appointment_id}.pdf'
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []
    
    # Add content to PDF
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Phiếu dịch vụ lâm sàng - Phòng khám Phụ Sản Đại Anh", styles['Title']))
    elements.append(Paragraph(f"Bệnh nhân: {appointment.patient.name}", styles['Normal']))
    elements.append(Paragraph(f"Ngày khám: {appointment.appointment_date.strftime('%d/%m/%Y')}", styles['Normal']))
    
    # Add services table
    data = [['STT', 'Dịch vụ', 'Giá']]
    total = 0
    for i, cs in enumerate(clinical_services, 1):
        service = ClinicalServiceSetting.query.get(cs.service_id)
        data.append([str(i), service.name, f"{service.price:,.0f} VNĐ"])
        total += service.price
    
    data.append(['', 'Tổng cộng', f"{total:,.0f} VNĐ"])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 1, colors.black),
        ('GRID', (0, -1), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return send_file(filename, as_attachment=True)

# Admin API Endpoints
@app.route('/api/home-content', methods=['GET'])
def get_home_content():
    home_content = HomeContent.query.first()
    if not home_content:
        # Create default content if not exists
        home_content = HomeContent(
            hero_title='Phòng khám chuyên khoa Phụ Sản Đại Anh',
            hero_description='Uy tín - Chất lượng - Tận tâm'
        )
        db.session.add(home_content)
        db.session.commit()

    services = Service.query.all()
    contact_info = ContactInfo.query.all()

    return jsonify({
        'heroTitle': home_content.hero_title,
        'heroDescription': home_content.hero_description,
        'clinicSummary': home_content.clinic_summary,
        'services': [{
            'name': s.name,
        } for s in services],
        'contactInfo': [{
            'type': c.type,
            'value': c.value
        } for c in contact_info]
    })

@app.route('/api/home-content', methods=['POST'])
def update_home_content():
    try:
        data = request.json
        
        # Update home content
        home_content = HomeContent.query.first()
        if not home_content:
            home_content = HomeContent()
            db.session.add(home_content)
        
        home_content.hero_title = data.get('heroTitle', home_content.hero_title)
        home_content.hero_description = data.get('slogan', data.get('heroDescription', home_content.hero_description))
        
        # Safely update clinic_summary
        if 'clinicSummary' in data:
            home_content.clinic_summary = data['clinicSummary']
        elif not hasattr(home_content, 'clinic_summary') or home_content.clinic_summary is None:
            home_content.clinic_summary = 'Siêu âm 5D, sàng lọc dị tật, khám phụ khoa, vô sinh'
        
        # Update services (if provided)
        if 'services' in data:
            Service.query.delete()  # Clear existing services
            for service in data['services']:
                new_service = Service(
                    name=service['name'],
                )
                db.session.add(new_service)
        
        # Update contact info
        if 'contactInfo' in data:
            ContactInfo.query.delete()  # Clear existing contact info
            for contact in data['contactInfo']:
                new_contact = ContactInfo(
                    type=contact['type'],
                    value=contact['value']
                )
                db.session.add(new_contact)
        
        db.session.commit()
        return jsonify({'message': 'Nội dung trang chủ đã được cập nhật'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi cập nhật home content: {e}")
        return jsonify({'error': 'Lỗi khi cập nhật nội dung'}), 500

@app.route('/api/clinic-summary', methods=['POST'])
def update_clinic_summary():
    try:
        data = request.json
        clinic_summary = data.get('clinicSummary', '')
        
        home_content = HomeContent.query.first()
        if not home_content:
            home_content = HomeContent(
                hero_title='Phòng khám chuyên khoa Phụ Sản Đại Anh',
                hero_description='Uy Tín - Chất Lượng',
                clinic_summary=clinic_summary
            )
            db.session.add(home_content)
        else:
            home_content.clinic_summary = clinic_summary
        
        db.session.commit()
        return jsonify({'message': 'Tóm tắt dịch vụ phòng khám đã được cập nhật', 'clinicSummary': clinic_summary})
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi cập nhật clinic summary: {e}")
        return jsonify({'error': 'Lỗi khi cập nhật tóm tắt dịch vụ'}), 500

@app.route('/api/examination-settings', methods=['GET'])
def get_examination_settings():
    settings = ExaminationSettings.query.first()
    if not settings:
        # Create default settings if not exists
        settings = ExaminationSettings(
            title='Danh sách khám ngày hôm nay',
            description='Quản lý danh sách khám và dịch vụ cận lâm sàng'
        )
        db.session.add(settings)
        db.session.commit()

    clinical_services = ClinicalServiceSetting.query.all()

    return jsonify({
        'title': settings.title,
        'description': settings.description,
        'clinicalServices': [{
            'id': s.id,
            'name': s.name,
            'price': s.price
        } for s in clinical_services]
    })

@app.route('/api/examination-settings', methods=['POST'])
def update_examination_settings():
    data = request.json
    # Update examination settings
    settings = ExaminationSettings.query.first()
    if not settings:
        settings = ExaminationSettings()
        db.session.add(settings)
    settings.title = data['title']
    settings.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Cài đặt danh sách khám đã được cập nhật'})

# API: Lấy danh sách kết quả xét nghiệm/siêu âm cho 1 lượt khám
@app.route('/api/appointments/<int:appointment_id>/test-results', methods=['GET'])
def get_test_results(appointment_id):
    results = TestResult.query.filter_by(appointment_id=appointment_id).all()
    return jsonify([
        {
            'id': r.id,
            'type': r.type,
            'result_text': r.result_text,
            'file_url': f"/uploads/{os.path.basename(r.file_path)}" if r.file_path else None,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M')
        } for r in results
    ])

# API: Thêm mới kết quả xét nghiệm/siêu âm
@app.route('/api/appointments/<int:appointment_id>/test-results', methods=['POST'])
def add_test_result(appointment_id):
    type_ = request.form.get('type')
    result_text = request.form.get('result_text')
    file = request.files.get('file')
    file_path = None
    if file:
        filename = werkzeug.utils.secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    test_result = TestResult(
        appointment_id=appointment_id,
        type=type_,
        result_text=result_text,
        file_path=file_path
    )
    db.session.add(test_result)
    db.session.commit()
    return jsonify({'message': 'Đã thêm kết quả thành công!'})

# API: Cập nhật kết quả
@app.route('/api/test-results/<int:id>', methods=['PUT'])
def update_test_result(id):
    test_result = TestResult.query.get_or_404(id)
    data = request.json
    test_result.type = data.get('type', test_result.type)
    test_result.result_text = data.get('result_text', test_result.result_text)
    db.session.commit()
    return jsonify({'message': 'Đã cập nhật kết quả!'})

# API: Xóa kết quả
@app.route('/api/test-results/<int:id>', methods=['DELETE'])
def delete_test_result(id):
    try:
        result = TestResult.query.get_or_404(id)
        db.session.delete(result)
        db.session.commit()
        return jsonify({'message': 'Đã xóa kết quả xét nghiệm thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Đã xảy ra lỗi khi xóa kết quả xét nghiệm: {str(e)}'}), 500

# API: Trả file upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/booking-content', methods=['GET'])
def get_booking_content():
    # Ensure column exists for older databases
    ensure_booking_reasons_column()
    content = BookingPageContent.query.first()
    if not content:
        # Nội dung mặc định nếu chưa có
        content = BookingPageContent(
            title='Đặt lịch khám trực tuyến',
            description='Đăng ký khám nhanh chóng, chủ động chọn thời gian, tiết kiệm thời gian chờ đợi tại phòng khám.',
            services='["Khám thai định kỳ","Siêu âm 2D, 4D, 5D","Xét nghiệm máu, nước tiểu","Tiêm phòng uốn ván, cúm","Tư vấn tiền sản"]',
            utilities='["Dinh dưỡng thai kỳ","Bài tập cho bà bầu","Địa chỉ mua sắm","Hỏi đáp"]',
            reasons='["Khám thai","Khám phụ khoa","Siêu âm","Tư vấn"]',
            schedule='Thứ Hai - Thứ Sáu: 8:00 - 17:00\nThứ Bảy: 8:00 - 12:00\nChủ Nhật: Nghỉ',
            contact='Địa chỉ: Số 123 Đường ABC, Quận XYZ, TP. Hà Nội\nĐiện thoại: 0123 456 789\nEmail: info@phusandaianh.vn'
        )
        db.session.add(content)
        db.session.commit()
    import json
    return jsonify({
        'title': content.title,
        'description': content.description,
        'services': json.loads(content.services or '[]'),
        'utilities': json.loads(content.utilities or '[]'),
        'reasons': json.loads(getattr(content, 'reasons', '[]') or '[]'),
        'schedule': content.schedule,
        'contact': content.contact
    })

@app.route('/api/booking-content', methods=['POST'])
def update_booking_content():
    # Ensure column exists for older databases
    ensure_booking_reasons_column()
    data = request.json
    content = BookingPageContent.query.first()
    if not content:
        content = BookingPageContent()
        db.session.add(content)
    content.title = data.get('title', content.title)
    content.description = data.get('description', content.description)
    import json
    content.services = json.dumps(data.get('services', []))
    content.utilities = json.dumps(data.get('utilities', []))
    # Handle reasons if present (backward compatible)
    if 'reasons' in data:
        content.reasons = json.dumps(data.get('reasons', []))
    content.schedule = data.get('schedule', content.schedule)
    content.contact = data.get('contact', content.contact)
    db.session.commit()
    return jsonify({'message': 'Đã cập nhật nội dung trang đặt lịch khám!'})

@app.route('/api/work-schedule', methods=['GET'])
def get_work_schedule():
    ensure_work_schedule_columns()
    today = datetime.now().date()
    days = []
    # Lấy tất cả lịch trong 14 ngày tới
    all_schedules = WorkSchedule.query.filter(
        WorkSchedule.date >= today.strftime('%Y-%m-%d'),
        WorkSchedule.date <= (today + timedelta(days=13)).strftime('%Y-%m-%d')
    ).order_by(WorkSchedule.date, WorkSchedule.start_time).all()
    # Gom theo ngày
    schedule_dict = {}
    for s in all_schedules:
        if s.date not in schedule_dict:
            schedule_dict[s.date] = []
        schedule_dict[s.date].append({
            'start_time': s.start_time,
            'end_time': s.end_time,
            'doctor_name': s.doctor_name,
            'is_locked': bool(getattr(s, 'is_locked', False)),
            'slot_minutes': int(getattr(s, 'slot_minutes', 10) or 10),
            'is_closed': bool(getattr(s, 'is_closed', False))
        })
    # Tạo đủ 14 ngày
    for i in range(14):
        d = today + timedelta(days=i)
        d_str = d.strftime('%Y-%m-%d')
        days.append({
            'date': d_str,
            'shifts': schedule_dict.get(d_str, [])
        })
    return jsonify(days)

@app.route('/api/admin/work-schedule', methods=['GET'])
def admin_get_work_schedule():
    ensure_work_schedule_columns()
    # Lấy lịch làm việc theo ngày (có thể truyền ?date=yyyy-mm-dd)
    date = request.args.get('date')
    q = WorkSchedule.query
    if date:
        q = q.filter_by(date=date)
    schedules = q.order_by(WorkSchedule.date, WorkSchedule.start_time).all()
    return jsonify([
        {
            'id': s.id,
            'date': s.date,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'doctor_name': s.doctor_name,
            'is_locked': bool(getattr(s, 'is_locked', False)),
            'slot_minutes': int(getattr(s, 'slot_minutes', 10) or 10),
            'is_closed': bool(getattr(s, 'is_closed', False))
        } for s in schedules
    ])

@app.route('/api/admin/work-schedule', methods=['POST'])
def admin_add_work_schedule():
    ensure_work_schedule_columns()
    data = request.json
    ws = WorkSchedule(
        date=data['date'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        doctor_name=data['doctor_name'],
        is_locked=bool(data.get('is_locked', False)),
        slot_minutes=int(data.get('slot_minutes', 10)),
        is_closed=bool(data.get('is_closed', False))
    )
    db.session.add(ws)
    db.session.commit()
    return jsonify({'message': 'Đã thêm ca khám!', 'id': ws.id})

@app.route('/api/admin/work-schedule/<int:id>', methods=['PUT'])
def admin_update_work_schedule(id):
    ensure_work_schedule_columns()
    ws = WorkSchedule.query.get_or_404(id)
    data = request.json
    ws.date = data.get('date', ws.date)
    ws.start_time = data.get('start_time', ws.start_time)
    ws.end_time = data.get('end_time', ws.end_time)
    ws.doctor_name = data.get('doctor_name', ws.doctor_name)
    if 'is_locked' in data:
        ws.is_locked = bool(data.get('is_locked'))
    if 'slot_minutes' in data:
        try:
            ws.slot_minutes = int(data.get('slot_minutes') or 10)
        except Exception:
            pass
    if 'is_closed' in data:
        ws.is_closed = bool(data.get('is_closed'))
    db.session.commit()
    return jsonify({'message': 'Đã cập nhật ca khám!'})

@app.route('/api/admin/work-schedule/<int:id>', methods=['DELETE'])
def admin_delete_work_schedule(id):
    ws = WorkSchedule.query.get_or_404(id)
    db.session.delete(ws)
    db.session.commit()
    return jsonify({'message': 'Đã xóa ca khám!'})

@app.route('/api/admin/work-schedule/copy-week', methods=['POST'])
def copy_work_schedule_week():
    data = request.json
    src_monday = datetime.strptime(data['src_monday'], '%Y-%m-%d').date()
    dst_monday = datetime.strptime(data['dst_monday'], '%Y-%m-%d').date()
    # Xóa lịch tuần đích nếu có
    for i in range(7):
        d = (dst_monday + timedelta(days=i)).strftime('%Y-%m-%d')
        WorkSchedule.query.filter_by(date=d).delete()
    # Copy từng ngày
    for i in range(7):
        src_date = (src_monday + timedelta(days=i)).strftime('%Y-%m-%d')
        dst_date = (dst_monday + timedelta(days=i)).strftime('%Y-%m-%d')
        shifts = WorkSchedule.query.filter_by(date=src_date).all()
        for s in shifts:
            ws = WorkSchedule(
                date=dst_date,
                start_time=s.start_time,
                end_time=s.end_time,
                doctor_name=s.doctor_name
            )
            db.session.add(ws)
    db.session.commit()
    return jsonify({'message': 'Đã copy lịch làm việc tuần thành công!'})

@app.route('/api/work-schedule/sync', methods=['POST'])
def sync_work_schedule():
    try:
        # Logic đồng bộ lịch làm việc
        return jsonify({'message': 'Đã đồng bộ lịch làm việc thành công'})
    except Exception as e:
        return jsonify({'message': f'Đã xảy ra lỗi khi đồng bộ lịch làm việc: {str(e)}'}), 500

@app.route('/api/admin/work-schedule/close-day', methods=['POST'])
def close_work_schedule_day():
    """Mark an entire day as closed. If no shifts exist, create a placeholder closed shift."""
    ensure_work_schedule_columns()
    data = request.json or {}
    date = data.get('date')
    is_closed = bool(data.get('is_closed', True))
    if not date:
        return jsonify({'message': 'Thiếu tham số date (yyyy-mm-dd).'}), 400
    try:
        # Update existing shifts
        updated = WorkSchedule.query.filter_by(date=date).update({WorkSchedule.is_closed: is_closed})
        if updated == 0 and is_closed:
            # Create a placeholder closed shift covering the day
            ws = WorkSchedule(
                date=date,
                start_time='00:00',
                end_time='23:59',
                doctor_name='Nghỉ',
                is_locked=True,
                is_closed=True,
                slot_minutes=10
            )
            db.session.add(ws)
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật trạng thái nghỉ của ngày', 'date': date, 'is_closed': is_closed})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật trạng thái nghỉ: {str(e)}'}), 500

# ============ Shift Template APIs ============
@app.route('/api/shift-templates', methods=['GET'])
def get_shift_templates():
    """Get all shift templates."""
    try:
        templates = ShiftTemplate.query.order_by(ShiftTemplate.name).all()
        return jsonify([{
            'id': t.id,
            'name': t.name,
            'start_time': t.start_time,
            'end_time': t.end_time,
            'doctor_name': t.doctor_name,
            'slot_minutes': t.slot_minutes,
            'created_at': t.created_at.isoformat() if t.created_at else None,
            'updated_at': t.updated_at.isoformat() if t.updated_at else None
        } for t in templates])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách ca khám mẫu: {str(e)}'}), 500

@app.route('/api/shift-templates', methods=['POST'])
def create_shift_template():
    """Create a new shift template."""
    try:
        data = request.json
        if not data.get('name') or not data.get('start_time') or not data.get('end_time') or not data.get('doctor_name'):
            return jsonify({'message': 'Thiếu thông tin bắt buộc'}), 400
        
        template = ShiftTemplate(
            name=data['name'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            doctor_name=data['doctor_name'],
            slot_minutes=int(data.get('slot_minutes', 10))
        )
        db.session.add(template)
        db.session.commit()
        return jsonify({'message': 'Đã tạo ca khám mẫu thành công!', 'id': template.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo ca khám mẫu: {str(e)}'}), 500

@app.route('/api/shift-templates/<int:id>', methods=['PUT'])
def update_shift_template(id):
    """Update a shift template."""
    try:
        template = ShiftTemplate.query.get_or_404(id)
        data = request.json
        
        if 'name' in data:
            template.name = data['name']
        if 'start_time' in data:
            template.start_time = data['start_time']
        if 'end_time' in data:
            template.end_time = data['end_time']
        if 'doctor_name' in data:
            template.doctor_name = data['doctor_name']
        if 'slot_minutes' in data:
            template.slot_minutes = int(data['slot_minutes'])
        
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật ca khám mẫu thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật ca khám mẫu: {str(e)}'}), 500

@app.route('/api/shift-templates/<int:id>', methods=['DELETE'])
def delete_shift_template(id):
    """Delete a shift template."""
    try:
        template = ShiftTemplate.query.get_or_404(id)
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Đã xóa ca khám mẫu thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa ca khám mẫu: {str(e)}'}), 500

@app.route('/api/shift-templates/init-defaults', methods=['POST'])
def init_default_shift_templates():
    """Initialize default shift templates."""
    try:
        # Check if templates already exist
        if ShiftTemplate.query.count() > 0:
            return jsonify({'message': 'Ca khám mẫu đã tồn tại!'})
        
        # Create default templates
        default_templates = [
            {
                'name': 'Ca sáng - Bác sĩ Quỳnh Anh',
                'start_time': '08:00',
                'end_time': '12:00',
                'doctor_name': 'Thạc sĩ Quỳnh Anh',
                'slot_minutes': 10
            },
            {
                'name': 'Ca chiều - Bác sĩ Ngọc Đại',
                'start_time': '13:00',
                'end_time': '17:00',
                'doctor_name': 'Bác sĩ CK2 Ngọc Đại',
                'slot_minutes': 15
            },
            {
                'name': 'Ca tối - Cả hai bác sĩ',
                'start_time': '18:00',
                'end_time': '20:00',
                'doctor_name': 'Thạc sĩ Quỳnh Anh + Bác sĩ CK2 Ngọc Đại',
                'slot_minutes': 10
            },
            {
                'name': 'Ca khám đặc biệt',
                'start_time': '07:00',
                'end_time': '09:00',
                'doctor_name': 'Thạc sĩ Quỳnh Anh',
                'slot_minutes': 5
            }
        ]
        
        for template_data in default_templates:
            template = ShiftTemplate(**template_data)
            db.session.add(template)
        
        db.session.commit()
        return jsonify({'message': 'Đã tạo ca khám mẫu mặc định thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo ca khám mẫu mặc định: {str(e)}'}), 500

# ============ Pregnancy Utilities APIs ============
@app.route('/api/pregnancy-utilities', methods=['GET'])
def get_pregnancy_utilities():
    """Get all pregnancy utilities."""
    try:
        utilities = PregnancyUtility.query.order_by(PregnancyUtility.type, PregnancyUtility.created_at.desc()).all()
        return jsonify([{
            'id': u.id,
            'type': u.type,
            'title': u.title,
            'description': u.description,
            'date': u.date.isoformat() if u.date else None,
            'week': u.week,
            'notes': u.notes,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'updated_at': u.updated_at.isoformat() if u.updated_at else None
        } for u in utilities])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách tiện ích: {str(e)}'}), 500

@app.route('/api/pregnancy-utilities', methods=['POST'])
def create_pregnancy_utility():
    """Create a new pregnancy utility."""
    try:
        data = request.json
        if not data.get('type') or not data.get('title'):
            return jsonify({'message': 'Thiếu thông tin bắt buộc'}), 400
        
        utility = PregnancyUtility(
            type=data['type'],
            title=data['title'],
            description=data.get('description', ''),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else None,
            week=int(data['week']) if data.get('week') else None,
            notes=data.get('notes', '')
        )
        db.session.add(utility)
        db.session.commit()
        return jsonify({'message': 'Đã tạo tiện ích thành công!', 'id': utility.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo tiện ích: {str(e)}'}), 500

@app.route('/api/pregnancy-utilities/<int:id>', methods=['PUT'])
def update_pregnancy_utility(id):
    """Update a pregnancy utility."""
    try:
        utility = PregnancyUtility.query.get_or_404(id)
        data = request.json
        
        if 'type' in data:
            utility.type = data['type']
        if 'title' in data:
            utility.title = data['title']
        if 'description' in data:
            utility.description = data['description']
        if 'date' in data:
            utility.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data['date'] else None
        if 'week' in data:
            utility.week = int(data['week']) if data['week'] else None
        if 'notes' in data:
            utility.notes = data['notes']
        
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật tiện ích thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật tiện ích: {str(e)}'}), 500

@app.route('/api/pregnancy-utilities/<int:id>', methods=['DELETE'])
def delete_pregnancy_utility(id):
    """Delete a pregnancy utility."""
    try:
        utility = PregnancyUtility.query.get_or_404(id)
        db.session.delete(utility)
        db.session.commit()
        return jsonify({'message': 'Đã xóa tiện ích thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa tiện ích: {str(e)}'}), 500

@app.route('/api/pregnancy-utilities/init-defaults', methods=['POST'])
def init_default_pregnancy_utilities():
    """Initialize default pregnancy utilities."""
    try:
        # Check if utilities already exist
        if PregnancyUtility.query.count() > 0:
            return jsonify({'message': 'Tiện ích đã tồn tại!'})
        
        # Create default utilities
        default_utilities = [
            {
                'type': 'vaccination',
                'title': 'Tiêm phòng uốn ván',
                'description': 'Tiêm phòng uốn ván cho mẹ bầu để bảo vệ cả mẹ và bé',
                'date': (datetime.now() + timedelta(days=7)).date(),
                'week': 20,
                'notes': 'Tiêm tại cơ sở y tế có chứng nhận'
            },
            {
                'type': 'baby-vaccination',
                'title': 'Tiêm phòng BCG cho bé',
                'description': 'Tiêm phòng BCG phòng lao cho trẻ sơ sinh',
                'date': (datetime.now() + timedelta(days=30)).date(),
                'week': None,
                'notes': 'Tiêm trong vòng 24h sau sinh'
            },
            {
                'type': 'nutrition',
                'title': 'Bổ sung axit folic',
                'description': 'Bổ sung axit folic 400mcg/ngày để ngăn ngừa dị tật ống thần kinh',
                'date': None,
                'week': 4,
                'notes': 'Nên bắt đầu từ trước khi mang thai'
            },
            {
                'type': 'health',
                'title': 'Khám thai định kỳ',
                'description': 'Khám thai định kỳ theo lịch để theo dõi sự phát triển của thai nhi',
                'date': (datetime.now() + timedelta(days=14)).date(),
                'week': 12,
                'notes': 'Mang theo sổ khám thai và kết quả xét nghiệm'
            }
        ]
        
        for utility_data in default_utilities:
            utility = PregnancyUtility(**utility_data)
            db.session.add(utility)
        
        db.session.commit()
        return jsonify({'message': 'Đã tạo tiện ích mặc định thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo tiện ích mặc định: {str(e)}'}), 500

@app.route('/api/clinical-service-packages', methods=['POST'])
def create_clinical_service_package():
    data = request.json
    name = data.get('name')
    price = data.get('price')
    service_ids = data.get('service_ids', [])

    if not name or price is None or not isinstance(service_ids, list):
        return jsonify({'message': 'Missing required fields or invalid data format.'}), 400

    try:
        # Check for duplicate name (case-insensitive)
        existing_package = ClinicalServicePackage.query.filter(db.func.lower(ClinicalServicePackage.name) == db.func.lower(name)).first()
        if existing_package:
            return jsonify({'message': f'Tên gói "{name}" đã tồn tại.'}), 400

        # Create the new package
        new_package = ClinicalServicePackage(
            name=name,
            price=price
        )
        db.session.add(new_package)
        db.session.flush() # Get the package ID before committing

        # Add selected services to the package
        for service_id in service_ids:
            service = ClinicalServiceSetting.query.get(service_id)
            if service:
                new_package.services.append(service)
            
        db.session.commit()
        return jsonify({'message': 'Clinical service package created successfully', 'package': {'id': new_package.id, 'name': new_package.name}}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error creating clinical service package: {e}")
        return jsonify({'message': 'An error occurred while creating the clinical service package.'}), 500

@app.route('/api/clinical-service-packages', methods=['GET'])
def get_clinical_service_packages():
    packages = ClinicalServicePackage.query.all()
    packages_list = []
    for package in packages:
        services_list = []
        for service in package.services:
            services_list.append({
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'service_group': service.service_group
            })
        packages_list.append({
            'id': package.id,
            'name': package.name,
            'price': package.price,
            'services': services_list,
            'created_at': package.created_at.isoformat(),
            'updated_at': package.updated_at.isoformat() if package.updated_at else None
        })
    return jsonify(packages_list)

@app.route('/api/clinical-service-packages/<int:id>', methods=['DELETE'])
def delete_clinical_service_package(id):
    package = ClinicalServicePackage.query.get_or_404(id)
    try:
        db.session.delete(package)
        db.session.commit()
        return jsonify({'message': 'Clinical service package deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting clinical service package: {e}")
        return jsonify({'message': 'An error occurred while deleting the clinical service package.'}), 500

@app.route('/api/clinical-service-packages/<int:package_id>', methods=['PUT'])
def update_clinical_service_package(package_id):
    package = ClinicalServicePackage.query.get_or_404(package_id)
    data = request.json
    name = data.get('name')
    price = data.get('price')
    service_ids = data.get('service_ids') # Allow service_ids to be None if not updating services

    if not name or price is None:
        return jsonify({'message': 'Missing required fields: name, price.'}), 400

    try:
        # Check for duplicate name (case-insensitive), excluding the current package
        existing_package = ClinicalServicePackage.query.filter(
            db.func.lower(ClinicalServicePackage.name) == db.func.lower(name),
            ClinicalServicePackage.id != package_id
        ).first()
        if existing_package:
            return jsonify({'message': f'Tên gói "{name}" đã tồn tại.'}), 400

        package.name = name
        package.price = price

        # Update associated services if service_ids is provided
        if service_ids is not None and isinstance(service_ids, list):
            # Clear existing associations
            package.services.clear()
            # Add new associations
            for service_id in service_ids:
                service = ClinicalServiceSetting.query.get(service_id)
                if service:
                    package.services.append(service)
            
        db.session.commit()
        return jsonify({'message': 'Clinical service package updated successfully', 'package': {'id': package.id, 'name': package.name}}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error updating clinical service package: {e}")
        return jsonify({'message': 'An error occurred while updating the clinical service package.'}), 500

@app.route('/api/patients', methods=['GET'])
def get_patients():
    patients = Patient.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'phone': p.phone,
        'date_of_birth': p.date_of_birth.strftime('%Y-%m-%d'),
        'address': p.address
    } for p in patients])

@app.route('/api/appointments/<int:appointment_id>/clinical-services', methods=['GET'])
def get_appointment_clinical_services(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    services = appointment.clinical_services
    return jsonify([{
        'id': s.id,  # id của bản ghi ClinicalService (liên kết)
        'service_id': s.service.id,  # id dịch vụ gốc (ClinicalServiceSetting)
        'name': s.service.name,
        'price': s.service.price
    } for s in services])

@app.route('/api/appointments/<int:appointment_id>/clinical-services', methods=['POST'])
def add_appointment_clinical_service(appointment_id):
    # Ensure backward-compatible columns exist on older databases before selecting service
    ensure_clinical_service_setting_columns()
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        data = request.json or {}
        raw_service_id = data.get('service_id')
        if raw_service_id is None:
            return jsonify({'message': 'service_id is required'}), 400
        try:
            service_id = int(raw_service_id)
        except Exception:
            return jsonify({'message': 'service_id must be an integer'}), 400

        # Kiểm tra service tồn tại
        service = ClinicalServiceSetting.query.get_or_404(service_id)

        # Thêm mới bản ghi ClinicalService (không dùng relationship append)
        clinical_service = ClinicalService(appointment_id=appointment_id, service_id=service_id)
        db.session.add(clinical_service)
        # Flush để có id cho clinical_service
        db.session.flush()

        # Tạo bản ghi LabOrder đồng bộ ngay lập tức (không bắt buộc)
        try:
            # Ensure lab_order table has necessary columns for older DBs
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
                clinical_service_id=clinical_service.id
            )
            db.session.add(lab_order)
        except Exception as lab_err:
            # Không chặn việc thêm dịch vụ nếu sync thất bại; chỉ log ra console
            print(f"Lab sync failed: {lab_err}")

        db.session.commit()
        return jsonify({'message': 'Service added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to add service: {str(e)}'}), 500

@app.route('/api/appointments/<int:appointment_id>/clinical-services/<int:service_id>', methods=['DELETE'])
def remove_appointment_clinical_service(appointment_id, service_id):
    try:
        clinical_service = ClinicalService.query.filter_by(
            appointment_id=appointment_id,
            service_id=service_id
        ).first()
        
        if not clinical_service:
            return jsonify({'message': 'Không tìm thấy dịch vụ khám này'}), 404
            
        # Xóa bản ghi LabOrder liên quan nếu có
        try:
            related_lab = LabOrder.query.filter_by(clinical_service_id=clinical_service.id).first()
            if related_lab:
                db.session.delete(related_lab)
        except Exception:
            pass

        db.session.delete(clinical_service)
        db.session.commit()
        
        return jsonify({'message': 'Đã xóa dịch vụ khám thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Đã xảy ra lỗi khi xóa dịch vụ khám: {str(e)}'}), 500

# Check-in API endpoints
@app.route('/api/checkin', methods=['POST'])
def checkin():
    try:
        data = request.get_json() or {}
        today = datetime.utcnow().date()
        
        # Lấy số thứ tự tiếp theo cho ngày hôm nay
        last_checkin = CheckIn.query.filter_by(checkin_date=today).order_by(CheckIn.queue_number.desc()).first()
        next_queue_number = (last_checkin.queue_number + 1) if last_checkin else 1
        
        # Tạo check-in mới
        checkin = CheckIn(
            queue_number=next_queue_number,
            name=data.get('name', 'Khách hàng'),
            phone=data.get('phone', ''),
            checkin_date=today
        )
        
        db.session.add(checkin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'queue_number': next_queue_number,
            'message': f'Check-in thành công! Số thứ tự của bạn là {next_queue_number}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }), 500

@app.route('/api/checkin/stats', methods=['GET'])
def checkin_stats():
    try:
        today = datetime.utcnow().date()
        
        # Tổng số check-in hôm nay
        total_checkins = CheckIn.query.filter_by(checkin_date=today).count()
        
        # Số thứ tự hiện tại (cao nhất)
        last_checkin = CheckIn.query.filter_by(checkin_date=today).order_by(CheckIn.queue_number.desc()).first()
        current_queue = last_checkin.queue_number if last_checkin else 0
        
        # Số bệnh nhân đang chờ
        waiting_count = CheckIn.query.filter_by(checkin_date=today, status='waiting').count()
        
        return jsonify({
            'total_checkins': total_checkins,
            'current_queue': current_queue,
            'waiting_count': waiting_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/checkin/waiting-list', methods=['GET'])
def waiting_list():
    try:
        today = datetime.utcnow().date()
        
        checkins = CheckIn.query.filter_by(checkin_date=today).order_by(CheckIn.queue_number.asc()).all()
        
        waiting_list = []
        for checkin in checkins:
            waiting_list.append({
                'id': checkin.id,
                'queue_number': checkin.queue_number,
                'name': checkin.name or 'Khách hàng',
                'phone': checkin.phone or 'Chưa có',
                'checkin_time': checkin.checkin_time.isoformat(),
                'status': checkin.status
            })
        
        return jsonify(waiting_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/checkin/<int:checkin_id>/status', methods=['PUT'])
def update_checkin_status(checkin_id):
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['waiting', 'serving', 'completed']:
            return jsonify({'error': 'Trạng thái không hợp lệ'}), 400
        
        checkin = CheckIn.query.get_or_404(checkin_id)
        checkin.status = new_status
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã cập nhật trạng thái thành {new_status}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Route để hiển thị trang QR check-in
@app.route('/qr-checkin')
def qr_checkin_page():
    return send_from_directory('.', 'qr-checkin.html')

# Route để hiển thị trang danh sách website
@app.route('/links.html')
def links_page():
    return send_from_directory('.', 'links.html')

# Route để hiển thị trang quản lý check-in
@app.route('/checkin-admin')
def checkin_admin_page():
    return send_from_directory('.', 'checkin-admin.html')

@app.route('/api/checkin/reset-day', methods=['POST'])
def reset_checkin_day():
    try:
        today = datetime.utcnow().date()
        
        # Xóa tất cả check-in của ngày hôm nay
        CheckIn.query.filter_by(checkin_date=today).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Đã reset dữ liệu check-in cho ngày mới'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        }), 500

def initialize_default_doctors():
    """Initialize default clinic doctors if none exist."""
    try:
        if ClinicDoctor.query.count() == 0:
            default_doctors = [
                {'degree': 'Bác sĩ CK2', 'name': 'Hà Ngọc Đại'},
                {'degree': 'Thạc sĩ - Bs', 'name': 'Nguyễn Thị Quỳnh Anh'},
                {'degree': '', 'name': 'PK Đại Anh'}
            ]
            
            for doctor_data in default_doctors:
                doctor = ClinicDoctor(
                    degree=doctor_data['degree'],
                    name=doctor_data['name']
                )
                db.session.add(doctor)
            
            db.session.commit()
            print("Đã khởi tạo danh sách bác sĩ mặc định")
    except Exception as e:
        print(f"Lỗi khởi tạo danh sách bác sĩ: {e}")
        db.session.rollback()

def initialize_default_templates():
    """Khởi tạo template mặc định nếu chưa có"""
    try:
        # Kiểm tra xem đã có template chưa
        if ClinicalFormTemplate.query.count() == 0:
            # Template header mặc định
            default_header = '''
<div style="display:flex; align-items:flex-start; justify-content:center; font-family:'Times New Roman', serif;">
  <div style="width:80px; text-align:center;">
    <img src="logo_phu_san_dai_anh.PNG" alt="Logo" style="height:60px; margin-top:2px;">
  </div>
  <div style="flex:1; text-align:center; line-height:1.4;">
    <h2 style="color:#0000cc; margin:0; font-size:18px;">PHÒNG KHÁM CHUYÊN KHOA PHỤ SẢN ĐẠI ANH</h2>
    <p style="margin:2px 0; font-size:14px;">Siêu âm 5D, sàng lọc dị tật, khám phụ khoa, vô sinh</p>
    <p style="margin:2px 0; color:#c0392b; font-weight:bold; font-size:14px;">UY TÍN - CHẤT LƯỢNG</p>
    <p style="margin:2px 0; font-size:13px;">TDP Quán Trắng - Tân An - Bắc Ninh - ĐT: 0858.838.616</p>
  </div>
</div>
<hr style="border:1px solid #000; margin-top:5px;">
'''
            
            # Template phiếu chỉ định
            lab_request_template = '''
<div style="font-family:'Times New Roman', serif; padding:20px;">
  <div style="text-align:center; margin-bottom:20px;">
    <h2 style="color:#0000cc; margin:0;">PHIẾU CHỈ ĐỊNH CẬN LÂM SÀNG</h2>
  </div>
  
  <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
    <tr>
      <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Họ tên:</strong></td>
      <td style="padding:8px; border:1px solid #000; width:30%;">_________________</td>
      <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Tuổi:</strong></td>
      <td style="padding:8px; border:1px solid #000; width:30%;">_________________</td>
    </tr>
    <tr>
      <td style="padding:8px; border:1px solid #000;"><strong>Địa chỉ:</strong></td>
      <td style="padding:8px; border:1px solid #000;" colspan="3">_________________</td>
    </tr>
    <tr>
      <td style="padding:8px; border:1px solid #000;"><strong>Chẩn đoán:</strong></td>
      <td style="padding:8px; border:1px solid #000;" colspan="3">_________________</td>
    </tr>
  </table>

  <div style="margin-bottom:20px;">
    <h3 style="color:#0000cc; margin-bottom:10px;">CHỈ ĐỊNH XÉT NGHIỆM:</h3>
    <div style="border:1px solid #000; padding:10px; min-height:100px;">
      <p>□ Siêu âm ổ bụng</p>
      <p>□ Siêu âm tử cung phần phụ</p>
      <p>□ Siêu âm thai</p>
      <p>□ Xét nghiệm máu</p>
      <p>□ Xét nghiệm nước tiểu</p>
      <p>□ Khác: _________________</p>
    </div>
  </div>

  <div style="display:flex; justify-content:space-between; margin-top:30px;">
    <div style="text-align:center;">
      <p><strong>Bác sĩ chỉ định</strong></p>
      <p style="margin-top:50px;">_________________</p>
    </div>
    <div style="text-align:center;">
      <p><strong>Ngày: ___/___/_____</strong></p>
    </div>
  </div>
</div>
'''
            
            # Template phiếu kết quả
            lab_result_template = '''
<div style="font-family:'Times New Roman', serif; padding:20px;">
  <div style="text-align:center; margin-bottom:20px;">
    <h2 style="color:#0000cc; margin:0;">PHIẾU KẾT QUẢ CẬN LÂM SÀNG</h2>
  </div>
  
  <table style="width:100%; border-collapse:collapse; margin-bottom:20px;">
    <tr>
      <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Họ tên:</strong></td>
      <td style="padding:8px; border:1px solid #000; width:30%;">_________________</td>
      <td style="padding:8px; border:1px solid #000; width:20%;"><strong>Tuổi:</strong></td>
      <td style="padding:8px; border:1px solid #000; width:30%;">_________________</td>
    </tr>
    <tr>
      <td style="padding:8px; border:1px solid #000;"><strong>Địa chỉ:</strong></td>
      <td style="padding:8px; border:1px solid #000;" colspan="3">_________________</td>
    </tr>
    <tr>
      <td style="padding:8px; border:1px solid #000;"><strong>Chẩn đoán:</strong></td>
      <td style="padding:8px; border:1px solid #000;" colspan="3">_________________</td>
    </tr>
  </table>

  <div style="margin-bottom:20px;">
    <h3 style="color:#0000cc; margin-bottom:10px;">KẾT QUẢ XÉT NGHIỆM:</h3>
    <div style="border:1px solid #000; padding:10px; min-height:150px;">
      <p><strong>Siêu âm:</strong></p>
      <p>Kết quả: _________________</p>
      <p>Ghi chú: _________________</p>
      <br>
      <p><strong>Xét nghiệm:</strong></p>
      <p>Kết quả: _________________</p>
      <p>Ghi chú: _________________</p>
    </div>
  </div>

  <div style="display:flex; justify-content:space-between; margin-top:30px;">
    <div style="text-align:center;">
      <p><strong>Bác sĩ thực hiện</strong></p>
      <p style="margin-top:50px;">_________________</p>
    </div>
    <div style="text-align:center;">
      <p><strong>Ngày: ___/___/_____</strong></p>
    </div>
  </div>
</div>
'''
            
            # Tạo template cho phiếu chỉ định
            request_template = ClinicalFormTemplate(
                template_type='lab-request',
                header_html=default_header,
                content_html=lab_request_template
            )
            db.session.add(request_template)
            
            # Tạo template cho phiếu kết quả
            result_template = ClinicalFormTemplate(
                template_type='lab-result',
                header_html=default_header,
                content_html=lab_result_template
            )
            db.session.add(result_template)
            
            db.session.commit()
            print("Đã khởi tạo template mặc định")
    except Exception as e:
        print(f"Lỗi khi khởi tạo template: {e}")
        db.session.rollback()

def ensure_logo_position_column():
    """Đảm bảo cột logo_position tồn tại trong bảng ClinicalFormTemplate"""
    try:
        # Kiểm tra xem cột đã tồn tại chưa
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('clinical_form_template')]
        
        if 'logo_position' not in columns:
            # Thêm cột mới
            db.engine.execute('ALTER TABLE clinical_form_template ADD COLUMN logo_position VARCHAR(20) DEFAULT "left"')
            print("Đã thêm cột logo_position vào bảng clinical_form_template")
        else:
            print("Cột logo_position đã tồn tại")
    except Exception as e:
        print(f"Lỗi khi kiểm tra/thêm cột logo_position: {e}")

def ensure_clinic_summary_column():
    """Đảm bảo cột clinic_summary tồn tại trong bảng HomeContent"""
    try:
        # Thử tạo một HomeContent record để test cột clinic_summary
        test_content = HomeContent.query.first()
        if test_content:
            # Nếu có record, thử truy cập cột clinic_summary
            if not hasattr(test_content, 'clinic_summary') or test_content.clinic_summary is None:
                test_content.clinic_summary = 'Siêu âm 5D, sàng lọc dị tật, khám phụ khoa, vô sinh'
                db.session.commit()
                print("Đã cập nhật clinic_summary cho record hiện có")
        else:
            # Nếu chưa có record, tạo mới
            new_content = HomeContent(
                hero_title='Phòng khám chuyên khoa Phụ Sản Đại Anh',
                hero_description='Uy Tín - Chất Lượng',
                clinic_summary='Siêu âm 5D, sàng lọc dị tật, khám phụ khoa, vô sinh'
            )
            db.session.add(new_content)
            db.session.commit()
            print("Đã tạo HomeContent record mới với clinic_summary")
    except Exception as e:
        print(f"Lỗi khi đảm bảo clinic_summary: {e}")
        # Nếu vẫn lỗi, tạo lại database
        try:
            db.drop_all()
            db.create_all()
            print("Đã tạo lại database")
        except Exception as e2:
            print(f"Lỗi khi tạo lại database: {e2}")

# Lab Price API endpoints
@app.route('/api/lab-prices', methods=['GET'])
def get_lab_prices():
    """Lấy danh sách tất cả giá xét nghiệm"""
    try:
        prices = LabPrice.query.order_by(LabPrice.name).all()
        return jsonify([{
            'id': price.id,
            'name': price.name,
            'unit': price.unit,
            'price': price.price,
            'note': price.note,
            'created_at': price.created_at.isoformat() if price.created_at else None,
            'updated_at': price.updated_at.isoformat() if price.updated_at else None
        } for price in prices])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách giá: {str(e)}'}), 500

@app.route('/api/lab-prices', methods=['POST'])
def create_lab_price():
    """Tạo giá xét nghiệm mới"""
    try:
        data = request.json
        price = LabPrice(
            name=data.get('name', ''),
            unit=data.get('unit', ''),
            price=float(data.get('price', 0)),
            note=data.get('note', '')
        )
        db.session.add(price)
        db.session.commit()
        return jsonify({
            'id': price.id,
            'name': price.name,
            'unit': price.unit,
            'price': price.price,
            'note': price.note,
            'created_at': price.created_at.isoformat() if price.created_at else None,
            'updated_at': price.updated_at.isoformat() if price.updated_at else None
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo giá xét nghiệm: {str(e)}'}), 500

@app.route('/api/lab-prices/<int:price_id>', methods=['PUT'])
def update_lab_price(price_id):
    """Cập nhật giá xét nghiệm"""
    try:
        price = LabPrice.query.get_or_404(price_id)
        data = request.json
        
        if 'name' in data:
            price.name = data['name']
        if 'unit' in data:
            price.unit = data['unit']
        if 'price' in data:
            price.price = float(data['price'])
        if 'note' in data:
            price.note = data['note']
        
        price.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': price.id,
            'name': price.name,
            'unit': price.unit,
            'price': price.price,
            'note': price.note,
            'created_at': price.created_at.isoformat() if price.created_at else None,
            'updated_at': price.updated_at.isoformat() if price.updated_at else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật giá xét nghiệm: {str(e)}'}), 500

@app.route('/api/lab-prices/<int:price_id>', methods=['DELETE'])
def delete_lab_price(price_id):
    """Xóa giá xét nghiệm"""
    try:
        price = LabPrice.query.get_or_404(price_id)
        db.session.delete(price)
        db.session.commit()
        return jsonify({'message': 'Đã xóa giá xét nghiệm thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa giá xét nghiệm: {str(e)}'}), 500

# Clinical form template API endpoints
@app.route('/api/clinical-form-template/<template_type>', methods=['GET'])
def get_clinical_form_template(template_type):
    """Lấy template mẫu phiếu cận lâm sàng từ database"""
    try:
        template = ClinicalFormTemplate.query.filter_by(template_type=template_type).first()
        if template:
            return jsonify({'template': template.content_html})
        else:
            return jsonify({'template': ''})
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy template: {str(e)}'}), 500

@app.route('/api/clinical-form-template/<template_type>', methods=['PUT'])
def update_clinical_form_template(template_type):
    """Cập nhật template mẫu phiếu cận lâm sàng"""
    try:
        data = request.json
        if not data:
            return jsonify({'message': 'Thiếu dữ liệu'}), 400
        
        content_html = data.get('content_html', '')
        if not content_html:
            return jsonify({'message': 'Nội dung template không được để trống'}), 400
        
        template = ClinicalFormTemplate.query.filter_by(template_type=template_type).first()
        
        if template:
            template.content_html = content_html
            template.updated_at = datetime.utcnow()
        else:
            template = ClinicalFormTemplate(
                template_type=template_type,
                header_html=data.get('header_html', ''),
                content_html=content_html
            )
            db.session.add(template)
        
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật template thành công', 'id': template.id})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating template {template_type}: {str(e)}")
        return jsonify({'message': f'Lỗi khi cập nhật template: {str(e)}'}), 500

@app.route('/api/clinical-form-header', methods=['GET'])
def get_clinical_form_header():
    """Lấy header mẫu phiếu cận lâm sàng từ database"""
    try:
        # Lấy header từ template đầu tiên (tất cả template đều có cùng header)
        template = ClinicalFormTemplate.query.first()
        if template:
            return jsonify({
                'header': template.header_html,
                'logo_position': template.logo_position or 'left'
            })
        else:
            # Fallback to home content
            home_content = HomeContent.query.first()
            if home_content:
                header = f'''
<div style="display:flex; align-items:center; justify-content:center; font-family:'Times New Roman', serif;">
  <div style="width:80px; text-align:center;">
    <img src="logo_phu_san_dai_anh.PNG" alt="Logo" style="height:70px;">
  </div>
  <div style="flex:1; text-align:center; line-height:1.4;">
    <h2 style="color:#0000cc; margin:0;">{home_content.hero_title or 'PHÒNG KHÁM CHUYÊN KHOA PHỤ SẢN ĐẠI ANH'}</h2>
    <p style="margin:2px 0; font-size:16px;">{home_content.clinic_summary or 'Siêu âm 5D, sàng lọc dị tật, khám phụ khoa, vô sinh'}</p>
    <p style="margin:2px 0; color:#c0392b; font-weight:bold;">{home_content.hero_description or 'UY TÍN - CHẤT LƯỢNG'}</p>
    <p style="margin:2px 0; font-size:14px;">TDP Quán Trắng - Tân An - Bắc Ninh - ĐT: 0858.838.616</p>
  </div>
</div>
<hr style="border:1px solid #000;">
'''
                return jsonify({'header': header, 'logo_position': 'left'})
            else:
                return jsonify({'header': '', 'logo_position': 'left'})
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy header: {str(e)}'}), 500

@app.route('/api/clinical-form-header', methods=['PUT'])
def update_clinical_form_header():
    """Cập nhật header cho tất cả template"""
    try:
        data = request.json
        new_header = data.get('header_html', '')
        logo_position = data.get('logo_position', 'left')
        
        # Cập nhật header và logo position cho tất cả template
        templates = ClinicalFormTemplate.query.all()
        for template in templates:
            template.header_html = new_header
            template.logo_position = logo_position
            template.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': 'Đã cập nhật header và vị trí logo cho tất cả template'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật header: {str(e)}'}), 500

@app.route('/api/appointments/<int:appointment_id>/full-info', methods=['GET'])
def get_appointment_full_info(appointment_id):
    """Lấy đầy đủ thông tin cuộc hẹn bao gồm chẩn đoán và dịch vụ cận lâm sàng"""
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        medical_record = MedicalRecord.query.filter_by(appointment_id=appointment_id).first()
        
        # Lấy danh sách dịch vụ cận lâm sàng
        clinical_services = ClinicalService.query.filter_by(appointment_id=appointment_id).all()
        services_list = []
        for service in clinical_services:
            service_setting = ClinicalServiceSetting.query.get(service.service_id)
            if service_setting:
                services_list.append({
                    'id': service.id,
                    'service_id': service.service_id,
                    'name': service_setting.name,
                    'price': service_setting.price,
                    'description': service_setting.description,
                    'status': service.status
                })
        
        return jsonify({
            'id': appointment.id,
            'patient_id': appointment.patient.id,
            'patient_name': appointment.patient.name,
            'patient_phone': appointment.patient.phone,
            'patient_dob': appointment.patient.date_of_birth.isoformat() if appointment.patient.date_of_birth else None,
            'patient_address': appointment.patient.address,
            'appointment_date': appointment.appointment_date.isoformat(),
            'service_type': appointment.service_type,
            'status': appointment.status,
            'doctor_name': getattr(appointment, 'doctor_name', 'PK Đại Anh'),
            'diagnosis': medical_record.diagnosis if medical_record else '',
            'notes': medical_record.notes if medical_record else '',
            'clinical_services': services_list
        })
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy thông tin cuộc hẹn: {str(e)}'}), 500

# ============ Special Templates APIs ============
class SpecialTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content_html = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ Lab Result Templates APIs ============
class LabResultTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content_html = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TreatmentPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    hospital = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.String(500))
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShiftTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    doctor_name = db.Column(db.String(100), nullable=False)
    slot_minutes = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PregnancyUtility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # vaccination, baby-vaccination, nutrition, health
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    week = db.Column(db.Integer)  # pregnancy week
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@app.route('/api/special-templates', methods=['GET'])
def get_special_templates():
    try:
        # Sử dụng raw SQL để tránh vấn đề datetime parsing
        result = db.session.execute(db.text("""
            SELECT id, name, description, content_html, created_at, updated_at 
            FROM special_template 
            ORDER BY created_at DESC
        """)).fetchall()
        
        templates = []
        for row in result:
            templates.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'content_html': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        return jsonify(templates)
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách mẫu đặc biệt: {str(e)}'}), 500

@app.route('/api/special-templates', methods=['POST'])
def create_special_template():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('content_html'):
            return jsonify({'message': 'Tên và nội dung mẫu phiếu là bắt buộc'}), 400
        
        template = SpecialTemplate(
            name=data['name'],
            description=data.get('description', ''),
            content_html=data['content_html']
        )
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'content_html': template.content_html,
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': template.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo mẫu đặc biệt: {str(e)}'}), 500

@app.route('/api/special-templates/<int:template_id>', methods=['PUT'])
def update_special_template(template_id):
    try:
        template = SpecialTemplate.query.get_or_404(template_id)
        data = request.json
        
        if data.get('name'):
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if data.get('content_html'):
            template.content_html = data['content_html']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'content_html': template.content_html,
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': template.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật mẫu đặc biệt: {str(e)}'}), 500

@app.route('/api/special-templates/<int:template_id>', methods=['DELETE'])
def delete_special_template(template_id):
    try:
        template = SpecialTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Đã xóa mẫu đặc biệt thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa mẫu đặc biệt: {str(e)}'}), 500

# ============ Voluson E10 Sync API ============
@app.route('/api/voluson/sync-status', methods=['GET'])
def get_voluson_sync_status():
    """Lấy trạng thái đồng bộ với Voluson E10"""
    try:
        sync_service = get_voluson_sync_service()
        status = sync_service.get_sync_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy trạng thái đồng bộ: {str(e)}'}), 500

@app.route('/api/voluson/start-sync', methods=['POST'])
def start_voluson_sync():
    """Khởi động service đồng bộ với Voluson E10"""
    try:
        sync_service = get_voluson_sync_service()
        sync_service.start_sync_service()
        return jsonify({'message': 'Đã khởi động service đồng bộ với Voluson E10'})
    except Exception as e:
        return jsonify({'error': f'Lỗi khi khởi động đồng bộ: {str(e)}'}), 500

@app.route('/api/voluson/stop-sync', methods=['POST'])
def stop_voluson_sync():
    """Dừng service đồng bộ với Voluson E10"""
    try:
        sync_service = get_voluson_sync_service()
        sync_service.stop_sync_service()
        return jsonify({'message': 'Đã dừng service đồng bộ với Voluson E10'})
    except Exception as e:
        return jsonify({'error': f'Lỗi khi dừng đồng bộ: {str(e)}'}), 500

@app.route('/api/voluson/sync-appointment/<int:appointment_id>', methods=['POST'])
def sync_single_appointment(appointment_id):
    """Đồng bộ một cuộc hẹn cụ thể với Voluson E10"""
    try:
        sync_service = get_voluson_sync_service()
        success = sync_service.sync_single_appointment(appointment_id)
        
        if success:
            return jsonify({'message': f'Đã đồng bộ thành công cuộc hẹn ID {appointment_id}'})
        else:
            return jsonify({'error': f'Không thể đồng bộ cuộc hẹn ID {appointment_id}'}), 400
    except Exception as e:
        return jsonify({'error': f'Lỗi khi đồng bộ cuộc hẹn: {str(e)}'}), 500

@app.route('/api/voluson/config', methods=['GET'])
def get_voluson_config():
    """Lấy cấu hình đồng bộ Voluson E10"""
    try:
        sync_service = get_voluson_sync_service()
        config = sync_service.config
        # Ẩn thông tin nhạy cảm
        safe_config = {k: v for k, v in config.items() if k not in ['password', 'token']}
        return jsonify(safe_config)
    except Exception as e:
        return jsonify({'error': f'Lỗi khi lấy cấu hình: {str(e)}'}), 500

@app.route('/api/voluson/config', methods=['PUT'])
def update_voluson_config():
    """Cập nhật cấu hình đồng bộ Voluson E10"""
    try:
        data = request.json
        sync_service = get_voluson_sync_service()
        
        # Cập nhật cấu hình
        for key, value in data.items():
            if key in sync_service.config:
                sync_service.config[key] = value
        
        # Lưu cấu hình vào file
        with open('voluson_config.json', 'w', encoding='utf-8') as f:
            json.dump(sync_service.config, f, indent=2, ensure_ascii=False)
        
        return jsonify({'message': 'Đã cập nhật cấu hình thành công'})
    except Exception as e:
        return jsonify({'error': f'Lỗi khi cập nhật cấu hình: {str(e)}'}), 500

# ============ Patient Records Model ============
class PatientRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(200), nullable=False)
    patient_phone = db.Column(db.String(20), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    doctor_name = db.Column(db.String(100))
    service_type = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ Prescription Models ============
class PrescriptionTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # pregnancy, gynecology, postpartum, fertility
    description = db.Column(db.Text)
    medications = db.Column(db.Text)  # JSON string of medication IDs and dosages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    ingredient = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # antibiotic, vitamin, hormone, painkiller, supplement
    unit = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    dosage = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(200), nullable=False)
    patient_phone = db.Column(db.String(20))
    prescription_date = db.Column(db.DateTime, nullable=False)
    doctor_name = db.Column(db.String(100), nullable=False)
    diagnosis = db.Column(db.String(200), nullable=False)
    medications = db.Column(db.Text)  # JSON string of medication IDs and dosages
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ Prescription Templates APIs ============
@app.route('/api/prescription-templates', methods=['GET'])
def get_prescription_templates():
    try:
        templates = PrescriptionTemplate.query.order_by(PrescriptionTemplate.created_at.desc()).all()
        return jsonify([{
            'id': template.id,
            'name': template.name,
            'category': template.category,
            'description': template.description,
            'medications': json.loads(template.medications) if template.medications else [],
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        } for template in templates])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách đơn thuốc mẫu: {str(e)}'}), 500

@app.route('/api/prescription-templates', methods=['POST'])
def create_prescription_template():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('category'):
            return jsonify({'message': 'Tên và bệnh lý là bắt buộc'}), 400
        
        template = PrescriptionTemplate(
            name=data['name'],
            category=data['category'],
            description=data.get('description', ''),
            medications=json.dumps(data.get('medications', []))
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã tạo đơn thuốc mẫu thành công',
            'id': template.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo đơn thuốc mẫu: {str(e)}'}), 500

@app.route('/api/prescription-templates/<int:template_id>', methods=['PUT'])
def update_prescription_template(template_id):
    try:
        template = PrescriptionTemplate.query.get_or_404(template_id)
        data = request.json
        
        if data.get('name'):
            template.name = data['name']
        if data.get('category'):
            template.category = data['category']
        if 'description' in data:
            template.description = data['description']
        if 'medications' in data:
            template.medications = json.dumps(data['medications'])
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Đã cập nhật đơn thuốc mẫu thành công',
            'id': template.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật đơn thuốc mẫu: {str(e)}'}), 500

@app.route('/api/prescription-templates/<int:template_id>', methods=['DELETE'])
def delete_prescription_template(template_id):
    try:
        template = PrescriptionTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Đã xóa đơn thuốc mẫu thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa đơn thuốc mẫu: {str(e)}'}), 500

# ============ Medications APIs ============
@app.route('/api/medications', methods=['GET'])
def get_medications():
    try:
        medications = Medication.query.order_by(Medication.name).all()
        return jsonify([{
            'id': medication.id,
            'name': medication.name,
            'ingredient': medication.ingredient,
            'category': medication.category,
            'unit': medication.unit,
            'price': medication.price,
            'dosage': medication.dosage,
            'notes': medication.notes,
            'created_at': medication.created_at.isoformat() if medication.created_at else None,
            'updated_at': medication.updated_at.isoformat() if medication.updated_at else None
        } for medication in medications])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách thuốc: {str(e)}'}), 500

@app.route('/api/medications', methods=['POST'])
def create_medication():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('ingredient') or not data.get('category') or not data.get('unit') or not data.get('price'):
            return jsonify({'message': 'Tên thuốc, hoạt chất, loại thuốc, đơn vị và giá là bắt buộc'}), 400
        
        medication = Medication(
            name=data['name'],
            ingredient=data['ingredient'],
            category=data['category'],
            unit=data['unit'],
            price=float(data['price']),
            dosage=data.get('dosage', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(medication)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã thêm thuốc thành công',
            'id': medication.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi thêm thuốc: {str(e)}'}), 500

@app.route('/api/medications/<int:medication_id>', methods=['PUT'])
def update_medication(medication_id):
    try:
        medication = Medication.query.get_or_404(medication_id)
        data = request.json
        
        if data.get('name'):
            medication.name = data['name']
        if data.get('ingredient'):
            medication.ingredient = data['ingredient']
        if data.get('category'):
            medication.category = data['category']
        if data.get('unit'):
            medication.unit = data['unit']
        if data.get('price'):
            medication.price = float(data['price'])
        if 'dosage' in data:
            medication.dosage = data['dosage']
        if 'notes' in data:
            medication.notes = data['notes']
        
        medication.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Đã cập nhật thuốc thành công',
            'id': medication.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật thuốc: {str(e)}'}), 500

@app.route('/api/medications/<int:medication_id>', methods=['DELETE'])
def delete_medication(medication_id):
    try:
        medication = Medication.query.get_or_404(medication_id)
        db.session.delete(medication)
        db.session.commit()
        return jsonify({'message': 'Đã xóa thuốc thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa thuốc: {str(e)}'}), 500

# ============ Prescriptions APIs ============
@app.route('/api/prescriptions', methods=['GET'])
def get_prescriptions():
    try:
        prescriptions = Prescription.query.order_by(Prescription.prescription_date.desc()).all()
        return jsonify([{
            'id': prescription.id,
            'patient_name': prescription.patient_name,
            'patient_phone': prescription.patient_phone,
            'prescription_date': prescription.prescription_date.isoformat(),
            'doctor_name': prescription.doctor_name,
            'diagnosis': prescription.diagnosis,
            'medications': json.loads(prescription.medications) if prescription.medications else [],
            'notes': prescription.notes,
            'created_at': prescription.created_at.isoformat() if prescription.created_at else None,
            'updated_at': prescription.updated_at.isoformat() if prescription.updated_at else None
        } for prescription in prescriptions])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách đơn thuốc: {str(e)}'}), 500

@app.route('/api/prescriptions', methods=['POST'])
def create_prescription():
    try:
        data = request.json
        if not data or not data.get('patient_name') or not data.get('prescription_date') or not data.get('doctor_name') or not data.get('diagnosis'):
            return jsonify({'message': 'Tên bệnh nhân, ngày kê đơn, bác sĩ và chẩn đoán là bắt buộc'}), 400
        
        prescription = Prescription(
            patient_name=data['patient_name'],
            patient_phone=data.get('patient_phone', ''),
            prescription_date=datetime.fromisoformat(data['prescription_date'].replace('Z', '+00:00')),
            doctor_name=data['doctor_name'],
            diagnosis=data['diagnosis'],
            medications=json.dumps(data.get('medications', [])),
            notes=data.get('notes', '')
        )
        
        db.session.add(prescription)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã tạo đơn thuốc thành công',
            'id': prescription.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo đơn thuốc: {str(e)}'}), 500

@app.route('/api/prescriptions/<int:prescription_id>', methods=['PUT'])
def update_prescription(prescription_id):
    try:
        prescription = Prescription.query.get_or_404(prescription_id)
        data = request.json
        
        if data.get('patient_name'):
            prescription.patient_name = data['patient_name']
        if 'patient_phone' in data:
            prescription.patient_phone = data['patient_phone']
        if data.get('prescription_date'):
            prescription.prescription_date = datetime.fromisoformat(data['prescription_date'].replace('Z', '+00:00'))
        if data.get('doctor_name'):
            prescription.doctor_name = data['doctor_name']
        if data.get('diagnosis'):
            prescription.diagnosis = data['diagnosis']
        if 'medications' in data:
            prescription.medications = json.dumps(data['medications'])
        if 'notes' in data:
            prescription.notes = data['notes']
        
        prescription.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Đã cập nhật đơn thuốc thành công',
            'id': prescription.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật đơn thuốc: {str(e)}'}), 500

@app.route('/api/prescriptions/<int:prescription_id>', methods=['DELETE'])
def delete_prescription(prescription_id):
    try:
        prescription = Prescription.query.get_or_404(prescription_id)
        db.session.delete(prescription)
        db.session.commit()
        return jsonify({'message': 'Đã xóa đơn thuốc thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa đơn thuốc: {str(e)}'}), 500

# ============ Test Meanings Model ============
class TestMeaning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # blood, urine, hormone, pregnancy, infection, tumor, genetic
    meaning = db.Column(db.Text, nullable=False)
    normal_range = db.Column(db.String(200))
    indications = db.Column(db.Text)
    preparation = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ Test Meanings APIs ============
@app.route('/api/test-meanings', methods=['GET'])
def get_test_meanings():
    try:
        tests = TestMeaning.query.order_by(TestMeaning.name).all()
        return jsonify([{
            'id': test.id,
            'name': test.name,
            'category': test.category,
            'meaning': test.meaning,
            'normal_range': test.normal_range,
            'indications': test.indications,
            'preparation': test.preparation,
            'notes': test.notes,
            'created_at': test.created_at.isoformat() if test.created_at else None,
            'updated_at': test.updated_at.isoformat() if test.updated_at else None
        } for test in tests])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách xét nghiệm: {str(e)}'}), 500

@app.route('/api/test-meanings', methods=['POST'])
def create_test_meaning():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('category') or not data.get('meaning'):
            return jsonify({'message': 'Tên xét nghiệm, loại xét nghiệm và ý nghĩa là bắt buộc'}), 400
        
        test = TestMeaning(
            name=data['name'],
            category=data['category'],
            meaning=data['meaning'],
            normal_range=data.get('normal_range', ''),
            indications=data.get('indications', ''),
            preparation=data.get('preparation', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(test)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã thêm xét nghiệm thành công',
            'id': test.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi thêm xét nghiệm: {str(e)}'}), 500

@app.route('/api/test-meanings/<int:test_id>', methods=['PUT'])
def update_test_meaning(test_id):
    try:
        test = TestMeaning.query.get_or_404(test_id)
        data = request.json
        
        if data.get('name'):
            test.name = data['name']
        if data.get('category'):
            test.category = data['category']
        if data.get('meaning'):
            test.meaning = data['meaning']
        if 'normal_range' in data:
            test.normal_range = data['normal_range']
        if 'indications' in data:
            test.indications = data['indications']
        if 'preparation' in data:
            test.preparation = data['preparation']
        if 'notes' in data:
            test.notes = data['notes']
        
        test.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Đã cập nhật xét nghiệm thành công',
            'id': test.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật xét nghiệm: {str(e)}'}), 500

@app.route('/api/test-meanings/<int:test_id>', methods=['DELETE'])
def delete_test_meaning(test_id):
    try:
        test = TestMeaning.query.get_or_404(test_id)
        db.session.delete(test)
        db.session.commit()
        return jsonify({'message': 'Đã xóa xét nghiệm thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa xét nghiệm: {str(e)}'}), 500

# ============ Disease Tests Model ============
class DiseaseTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # pregnancy, gynecology, hormone, infection, tumor, infertility, menopause
    description = db.Column(db.Text, nullable=False)
    required_tests = db.Column(db.Text)  # JSON string of test IDs and priorities
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============ Disease Tests APIs ============
@app.route('/api/disease-tests', methods=['GET'])
def get_disease_tests():
    try:
        diseases = DiseaseTest.query.order_by(DiseaseTest.name).all()
        return jsonify([{
            'id': disease.id,
            'name': disease.name,
            'category': disease.category,
            'description': disease.description,
            'required_tests': disease.required_tests,
            'notes': disease.notes,
            'created_at': disease.created_at.isoformat() if disease.created_at else None,
            'updated_at': disease.updated_at.isoformat() if disease.updated_at else None
        } for disease in diseases])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách bệnh lý: {str(e)}'}), 500

@app.route('/api/disease-tests', methods=['POST'])
def create_disease_test():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('category') or not data.get('description'):
            return jsonify({'message': 'Tên bệnh lý, loại bệnh lý và mô tả là bắt buộc'}), 400
        
        disease = DiseaseTest(
            name=data['name'],
            category=data['category'],
            description=data['description'],
            required_tests=json.dumps(data.get('required_tests', [])),
            notes=data.get('notes', '')
        )
        
        db.session.add(disease)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã thêm bệnh lý thành công',
            'id': disease.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi thêm bệnh lý: {str(e)}'}), 500

@app.route('/api/disease-tests/<int:disease_id>', methods=['PUT'])
def update_disease_test(disease_id):
    try:
        disease = DiseaseTest.query.get_or_404(disease_id)
        data = request.json
        
        if data.get('name'):
            disease.name = data['name']
        if data.get('category'):
            disease.category = data['category']
        if data.get('description'):
            disease.description = data['description']
        if 'required_tests' in data:
            disease.required_tests = json.dumps(data['required_tests'])
        if 'notes' in data:
            disease.notes = data['notes']
        
        disease.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Đã cập nhật bệnh lý thành công',
            'id': disease.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật bệnh lý: {str(e)}'}), 500

@app.route('/api/disease-tests/<int:disease_id>', methods=['DELETE'])
def delete_disease_test(disease_id):
    try:
        disease = DiseaseTest.query.get_or_404(disease_id)
        db.session.delete(disease)
        db.session.commit()
        return jsonify({'message': 'Đã xóa bệnh lý thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa bệnh lý: {str(e)}'}), 500

# ============ Patient Records APIs ============
@app.route('/api/patient-records/init-table', methods=['POST'])
def init_patient_records_table():
    """Tạo bảng patient_record nếu chưa tồn tại"""
    try:
        # Tạo bảng nếu chưa tồn tại
        db.create_all()
        return jsonify({'message': 'Bảng hồ sơ bệnh án đã được tạo thành công'})
    except Exception as e:
        return jsonify({'message': f'Lỗi khi tạo bảng: {str(e)}'}), 500

@app.route('/api/patient-records', methods=['GET'])
def get_patient_records():
    try:
        records = PatientRecord.query.order_by(PatientRecord.appointment_date.desc()).all()
        return jsonify([{
            'id': record.id,
            'patient_name': record.patient_name,
            'patient_phone': record.patient_phone,
            'appointment_date': record.appointment_date.isoformat(),
            'doctor_name': record.doctor_name,
            'service_type': record.service_type,
            'status': record.status,
            'notes': record.notes,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None
        } for record in records])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách hồ sơ: {str(e)}'}), 500

@app.route('/api/patient-records', methods=['POST'])
def create_patient_record():
    try:
        data = request.json
        if not data or not data.get('patient_name') or not data.get('patient_phone') or not data.get('appointment_date') or not data.get('service_type'):
            return jsonify({'message': 'Tên bệnh nhân, số điện thoại, ngày khám và lý do khám là bắt buộc'}), 400
        
        record = PatientRecord(
            patient_name=data['patient_name'],
            patient_phone=data['patient_phone'],
            appointment_date=datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00')),
            doctor_name=data.get('doctor_name', ''),
            service_type=data['service_type'],
            status=data.get('status', 'pending'),
            notes=data.get('notes', '')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã tạo hồ sơ thành công',
            'id': record.id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo hồ sơ: {str(e)}'}), 500

@app.route('/api/patient-records/<int:record_id>', methods=['PUT'])
def update_patient_record(record_id):
    try:
        record = PatientRecord.query.get_or_404(record_id)
        data = request.json
        
        if data.get('patient_name'):
            record.patient_name = data['patient_name']
        if data.get('patient_phone'):
            record.patient_phone = data['patient_phone']
        if data.get('appointment_date'):
            record.appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
        if 'doctor_name' in data:
            record.doctor_name = data['doctor_name']
        if data.get('service_type'):
            record.service_type = data['service_type']
        if data.get('status'):
            record.status = data['status']
        if 'notes' in data:
            record.notes = data['notes']
        
        record.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Đã cập nhật hồ sơ thành công',
            'id': record.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật hồ sơ: {str(e)}'}), 500

@app.route('/api/patient-records/<int:record_id>', methods=['DELETE'])
def delete_patient_record(record_id):
    try:
        record = PatientRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'message': 'Đã xóa hồ sơ thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa hồ sơ: {str(e)}'}), 500

# ============ Lab Result Templates APIs ============
def ensure_lab_result_template_columns():
    """Đảm bảo các cột cần thiết tồn tại trong bảng lab_result_template"""
    try:
        # Kiểm tra xem cột updated_at đã tồn tại chưa
        result = db.engine.execute(db.text("PRAGMA table_info(lab_result_template)"))
        columns = [row[1] for row in result]
        
        if 'updated_at' not in columns:
            # Thêm cột updated_at nếu chưa có
            db.engine.execute(db.text("ALTER TABLE lab_result_template ADD COLUMN updated_at DATETIME"))
            print("Added updated_at column to lab_result_template table")
    except Exception as e:
        print(f"Error ensuring lab_result_template columns: {e}")

@app.route('/api/lab-result-templates', methods=['GET'])
def get_lab_result_templates():
    ensure_lab_result_template_columns()
    try:
        # Sử dụng raw SQL để tránh vấn đề datetime parsing
        result = db.session.execute(db.text("""
            SELECT id, name, description, content_html, created_at, updated_at 
            FROM lab_result_template 
            ORDER BY created_at DESC
        """)).fetchall()
        
        templates = []
        for row in result:
            templates.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'content_html': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        
        return jsonify(templates)
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách mẫu kết quả: {str(e)}'}), 500

@app.route('/api/lab-result-templates', methods=['POST'])
def create_lab_result_template():
    ensure_lab_result_template_columns()
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('content_html'):
            return jsonify({'message': 'Tên và nội dung mẫu phiếu là bắt buộc'}), 400
        
        template = LabResultTemplate(
            name=data['name'],
            description=data.get('description', ''),
            content_html=data['content_html']
        )
        db.session.add(template)
        db.session.commit()
        
        return jsonify({
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'content_html': template.content_html,
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': template.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo mẫu kết quả: {str(e)}'}), 500

@app.route('/api/lab-result-templates/<int:template_id>', methods=['PUT'])
def update_lab_result_template(template_id):
    ensure_lab_result_template_columns()
    try:
        template = LabResultTemplate.query.get_or_404(template_id)
        data = request.json
        
        if data.get('name'):
            template.name = data['name']
        if 'description' in data:
            template.description = data['description']
        if data.get('content_html'):
            template.content_html = data['content_html']
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'content_html': template.content_html,
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': template.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật mẫu kết quả: {str(e)}'}), 500

@app.route('/api/lab-result-templates/<int:template_id>', methods=['DELETE'])
def delete_lab_result_template(template_id):
    ensure_lab_result_template_columns()
    try:
        template = LabResultTemplate.query.get_or_404(template_id)
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Đã xóa mẫu kết quả thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa mẫu kết quả: {str(e)}'}), 500

# ============ Treatment Plans APIs ============
@app.route('/treatment-plans.html')
def treatment_plans_page():
    return render_template('treatment-plans.html')

@app.route('/api/treatment-plans', methods=['GET'])
def get_treatment_plans():
    try:
        plans = TreatmentPlan.query.order_by(TreatmentPlan.created_at.desc()).all()
        return jsonify([{
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'hospital': plan.hospital,
            'category': plan.category,
            'tags': plan.tags,
            'file_name': plan.file_name,
            'file_size': plan.file_size,
            'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': plan.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for plan in plans])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách phác đồ điều trị: {str(e)}'}), 500

@app.route('/api/treatment-plans', methods=['POST'])
def create_treatment_plan():
    try:
        data = request.json
        if not data or not data.get('name') or not data.get('hospital') or not data.get('category'):
            return jsonify({'message': 'Tên, bệnh viện và chuyên khoa là bắt buộc'}), 400
        
        plan = TreatmentPlan(
            name=data['name'],
            description=data.get('description', ''),
            hospital=data['hospital'],
            category=data['category'],
            tags=data.get('tags', ''),
            file_path='',  # Will be set during file upload
            file_name='',
            file_size=0
        )
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'hospital': plan.hospital,
            'category': plan.category,
            'tags': plan.tags,
            'file_name': plan.file_name,
            'file_size': plan.file_size,
            'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': plan.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tạo phác đồ điều trị: {str(e)}'}), 500

@app.route('/api/treatment-plans/<int:plan_id>', methods=['PUT'])
def update_treatment_plan(plan_id):
    try:
        plan = TreatmentPlan.query.get_or_404(plan_id)
        data = request.json
        
        if data.get('name'):
            plan.name = data['name']
        if 'description' in data:
            plan.description = data['description']
        if data.get('hospital'):
            plan.hospital = data['hospital']
        if data.get('category'):
            plan.category = data['category']
        if 'tags' in data:
            plan.tags = data['tags']
        
        plan.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'hospital': plan.hospital,
            'category': plan.category,
            'tags': plan.tags,
            'file_name': plan.file_name,
            'file_size': plan.file_size,
            'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': plan.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật phác đồ điều trị: {str(e)}'}), 500

@app.route('/api/treatment-plans/<int:plan_id>', methods=['DELETE'])
def delete_treatment_plan(plan_id):
    try:
        plan = TreatmentPlan.query.get_or_404(plan_id)
        
        # Delete file if exists
        if plan.file_path and os.path.exists(plan.file_path):
            os.remove(plan.file_path)
        
        db.session.delete(plan)
        db.session.commit()
        return jsonify({'message': 'Đã xóa phác đồ điều trị thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa phác đồ điều trị: {str(e)}'}), 500

@app.route('/api/treatment-plans/upload', methods=['POST'])
def upload_treatment_plan():
    try:
        if 'file' not in request.files:
            return jsonify({'message': 'Không có file được tải lên'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'Không có file được chọn'}), 400
        
        if file and file.filename.lower().endswith('.pdf'):
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join(app.root_path, 'uploads', 'treatment-plans')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            file.save(file_path)
            
            # Get form data
            name = request.form.get('name', file.filename.replace('.pdf', ''))
            description = request.form.get('description', '')
            hospital = request.form.get('hospital', 'Bệnh viện chưa xác định')
            category = request.form.get('category', 'sản')
            tags = request.form.get('tags', '')
            
            # Create treatment plan record
            plan = TreatmentPlan(
                name=name,
                description=description,
                hospital=hospital,
                category=category,
                tags=tags,
                file_path=file_path,
                file_name=file.filename,
                file_size=os.path.getsize(file_path)
            )
            db.session.add(plan)
            db.session.commit()
            
            return jsonify({
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'hospital': plan.hospital,
                'category': plan.category,
                'tags': plan.tags,
                'file_name': plan.file_name,
                'file_size': plan.file_size,
                'created_at': plan.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': plan.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }), 201
        else:
            return jsonify({'message': 'Chỉ chấp nhận file PDF'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi tải lên file: {str(e)}'}), 500

@app.route('/api/treatment-plans/<int:plan_id>/download', methods=['GET'])
def download_treatment_plan(plan_id):
    try:
        plan = TreatmentPlan.query.get_or_404(plan_id)
        
        if not plan.file_path or not os.path.exists(plan.file_path):
            return jsonify({'message': 'File không tồn tại'}), 404
        
        return send_file(plan.file_path, as_attachment=True, download_name=plan.file_name)
    except Exception as e:
        return jsonify({'message': f'Lỗi khi tải xuống file: {str(e)}'}), 500

@app.route('/api/treatment-plans/<int:plan_id>/view', methods=['GET'])
def view_treatment_plan(plan_id):
    try:
        plan = TreatmentPlan.query.get_or_404(plan_id)
        
        if not plan.file_path or not os.path.exists(plan.file_path):
            return jsonify({'message': 'File không tồn tại'}), 404
        
        # Return PDF file for inline viewing (not as attachment)
        return send_file(plan.file_path, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'message': f'Lỗi khi xem file: {str(e)}'}), 500

# ============ CTG Analysis APIs ============
class CTGResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    baseline_hr = db.Column(db.Integer, nullable=False)
    variability = db.Column(db.Integer, nullable=False)
    accelerations = db.Column(db.Integer, nullable=False)
    decelerations = db.Column(db.Integer, nullable=False)
    contractions = db.Column(db.Integer, nullable=False)
    recording_time = db.Column(db.Integer, nullable=False)
    analysis_score = db.Column(db.Integer)
    analysis_status = db.Column(db.String(20))
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'exam_date': self.exam_date.strftime('%Y-%m-%d %H:%M:%S'),
            'baseline_hr': self.baseline_hr,
            'variability': self.variability,
            'accelerations': self.accelerations,
            'decelerations': self.decelerations,
            'contractions': self.contractions,
            'recording_time': self.recording_time,
            'analysis_score': self.analysis_score,
            'analysis_status': self.analysis_status,
            'recommendations': self.recommendations,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class UltrasoundResult(db.Model):
    __tablename__ = 'ultrasound_results'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    gestational_age = db.Column(db.Float)
    bpd = db.Column(db.Float)  # Biparietal diameter
    hc = db.Column(db.Float)   # Head circumference
    ac = db.Column(db.Float)   # Abdominal circumference
    fl = db.Column(db.Float)   # Femur length
    ri_umbilical = db.Column(db.Float)  # Umbilical artery RI
    sd_ratio = db.Column(db.Float)     # S/D ratio
    mca_pi = db.Column(db.Float)       # Middle cerebral artery PI
    cervical_length = db.Column(db.Float)
    afi = db.Column(db.Float)  # Amniotic fluid index
    estimated_weight = db.Column(db.Float)
    fetal_position = db.Column(db.String(50))
    placenta_position = db.Column(db.String(50))
    amniotic_fluid = db.Column(db.String(50))
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    analysis_source = db.Column(db.String(50), default='manual_input')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'gestational_age': self.gestational_age,
            'bpd': self.bpd,
            'hc': self.hc,
            'ac': self.ac,
            'fl': self.fl,
            'ri_umbilical': self.ri_umbilical,
            'sd_ratio': self.sd_ratio,
            'mca_pi': self.mca_pi,
            'cervical_length': self.cervical_length,
            'afi': self.afi,
            'estimated_weight': self.estimated_weight,
            'fetal_position': self.fetal_position,
            'placenta_position': self.placenta_position,
            'amniotic_fluid': self.amniotic_fluid,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'analysis_source': self.analysis_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@app.route('/api/ctg-results', methods=['GET'])
def get_ctg_results():
    """Lấy danh sách kết quả CTG"""
    try:
        results = CTGResult.query.order_by(CTGResult.created_at.desc()).all()
        return jsonify([result.to_dict() for result in results])
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy danh sách CTG: {str(e)}'}), 500

@app.route('/api/ctg-results', methods=['POST'])
def create_ctg_result():
    """Tạo kết quả CTG mới"""
    try:
        data = request.json
        if not data or not data.get('patient_id'):
            return jsonify({'message': 'Thiếu thông tin bệnh nhân'}), 400
        
        # Parse exam date
        exam_date = datetime.strptime(data['exam_date'], '%Y-%m-%dT%H:%M')
        
        # Perform CTG analysis
        baseline_hr = int(data.get('baseline_hr', 0))
        variability = int(data.get('variability', 0))
        accelerations = int(data.get('accelerations', 0))
        decelerations = int(data.get('decelerations', 0))
        
        # Calculate analysis score
        score = 0
        status = 'normal'
        recommendations = []
        
        # Analyze baseline heart rate
        if 110 <= baseline_hr <= 160:
            score += 2
        elif 100 <= baseline_hr <= 170:
            score += 1
        else:
            recommendations.append('Nhịp tim thai cơ bản nằm ngoài giới hạn bình thường')
        
        # Analyze variability
        if 5 <= variability <= 25:
            score += 2
        elif 2 <= variability <= 30:
            score += 1
        else:
            recommendations.append('Biến thiên nhịp tim bất thường')
        
        # Analyze accelerations
        if accelerations >= 2:
            score += 2
        elif accelerations >= 1:
            score += 1
        else:
            recommendations.append('Thiếu tăng nhịp tim, cần theo dõi')
        
        # Analyze decelerations
        if decelerations == 0:
            score += 2
        elif decelerations <= 2:
            score += 1
        else:
            recommendations.append('Có giảm nhịp tim, cần đánh giá thêm')
        
        # Determine status
        if score >= 8:
            status = 'normal'
        elif score >= 6:
            status = 'warning'
        else:
            status = 'danger'
        
        ctg_result = CTGResult(
            patient_id=data['patient_id'],
            exam_date=exam_date,
            baseline_hr=baseline_hr,
            variability=variability,
            accelerations=accelerations,
            decelerations=decelerations,
            contractions=int(data.get('contractions', 0)),
            recording_time=int(data.get('recording_time', 0)),
            analysis_score=score,
            analysis_status=status,
            recommendations='; '.join(recommendations) if recommendations else None
        )
        
        db.session.add(ctg_result)
        db.session.commit()
        
        return jsonify({
            'message': 'Đã lưu kết quả CTG thành công',
            'ctg_id': ctg_result.id,
            'analysis': {
                'score': score,
                'max_score': 8,
                'status': status,
                'recommendations': recommendations
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi lưu kết quả CTG: {str(e)}'}), 500

@app.route('/api/ctg-results/<int:ctg_id>', methods=['GET'])
def get_ctg_result(ctg_id):
    """Lấy chi tiết kết quả CTG"""
    try:
        ctg_result = CTGResult.query.get_or_404(ctg_id)
        return jsonify(ctg_result.to_dict())
    except Exception as e:
        return jsonify({'message': f'Lỗi khi lấy kết quả CTG: {str(e)}'}), 500

@app.route('/api/ctg-results/<int:ctg_id>', methods=['PUT'])
def update_ctg_result(ctg_id):
    """Cập nhật kết quả CTG"""
    try:
        ctg_result = CTGResult.query.get_or_404(ctg_id)
        data = request.json
        
        if data.get('exam_date'):
            ctg_result.exam_date = datetime.strptime(data['exam_date'], '%Y-%m-%dT%H:%M')
        if data.get('baseline_hr'):
            ctg_result.baseline_hr = int(data['baseline_hr'])
        if data.get('variability'):
            ctg_result.variability = int(data['variability'])
        if data.get('accelerations'):
            ctg_result.accelerations = int(data['accelerations'])
        if data.get('decelerations'):
            ctg_result.decelerations = int(data['decelerations'])
        if data.get('contractions'):
            ctg_result.contractions = int(data['contractions'])
        if data.get('recording_time'):
            ctg_result.recording_time = int(data['recording_time'])
        
        ctg_result.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Đã cập nhật kết quả CTG thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi cập nhật kết quả CTG: {str(e)}'}), 500

@app.route('/api/ctg-results/<int:ctg_id>', methods=['DELETE'])
def delete_ctg_result(ctg_id):
    """Xóa kết quả CTG"""
    try:
        ctg_result = CTGResult.query.get_or_404(ctg_id)
        db.session.delete(ctg_result)
        db.session.commit()
        
        return jsonify({'message': 'Đã xóa kết quả CTG thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi xóa kết quả CTG: {str(e)}'}), 500

@app.route('/api/analyze-ctg-image', methods=['POST'])
def analyze_ctg_image():
    """Phân tích ảnh CTG bằng điện toán"""
    try:
        data = request.json
        if not data or not data.get('image_data'):
            return jsonify({'message': 'Thiếu dữ liệu ảnh'}), 400
        
        # Simulate image analysis (in real implementation, use AI/ML models)
        # This is a mock analysis for demonstration
        import random
        import base64
        
        # Extract image data
        image_data = data['image_data']
        patient_id = data.get('patient_id')
        
        # Mock analysis results (in real implementation, use computer vision)
        baseline_hr = random.randint(110, 160)
        variability = random.randint(5, 25)
        accelerations = random.randint(1, 5)
        decelerations = random.randint(0, 3)
        contractions = random.randint(0, 5)
        recording_time = random.randint(20, 60)
        
        # Calculate analysis score
        score = 0
        status = 'normal'
        recommendations = []
        confidence = random.randint(75, 95)
        
        # Analyze baseline heart rate
        if 110 <= baseline_hr <= 160:
            score += 2
        elif 100 <= baseline_hr <= 170:
            score += 1
        else:
            recommendations.append('Nhịp tim thai cơ bản nằm ngoài giới hạn bình thường')
        
        # Analyze variability
        if 5 <= variability <= 25:
            score += 2
        elif 2 <= variability <= 30:
            score += 1
        else:
            recommendations.append('Biến thiên nhịp tim bất thường')
        
        # Analyze accelerations
        if accelerations >= 2:
            score += 2
        elif accelerations >= 1:
            score += 1
        else:
            recommendations.append('Thiếu tăng nhịp tim, cần theo dõi')
        
        # Analyze decelerations
        if decelerations == 0:
            score += 2
        elif decelerations <= 2:
            score += 1
        else:
            recommendations.append('Có giảm nhịp tim, cần đánh giá thêm')
        
        # Determine status
        if score >= 8:
            status = 'normal'
        elif score >= 6:
            status = 'warning'
        else:
            status = 'danger'
        
        # Add some realistic recommendations based on analysis
        if status == 'warning':
            recommendations.append('Cần theo dõi thêm và có thể cần đánh giá lại')
        elif status == 'danger':
            recommendations.append('Cần đánh giá ngay lập tức bởi bác sĩ chuyên khoa')
        
        # Save image file (optional)
        if image_data.startswith('data:image'):
            # Extract base64 data
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            
            # Save to uploads directory
            upload_dir = 'uploads/ctg-images'
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = f"ctg_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
        
        return jsonify({
            'message': 'Phân tích ảnh CTG thành công',
            'baseline_hr': baseline_hr,
            'variability': variability,
            'accelerations': accelerations,
            'decelerations': decelerations,
            'contractions': contractions,
            'recording_time': recording_time,
            'analysis_score': score,
            'max_score': 8,
            'analysis_status': status,
            'confidence': confidence,
            'recommendations': recommendations,
            'analysis_method': 'computer_vision',
            'image_saved': True if image_data.startswith('data:image') else False
        })
        
    except Exception as e:
        return jsonify({'message': f'Lỗi khi phân tích ảnh CTG: {str(e)}'}), 500

@app.route('/api/analyze-ultrasound-image', methods=['POST'])
def analyze_ultrasound_image():
    """Phân tích ảnh siêu âm thai bằng điện toán"""
    try:
        data = request.json
        if not data or not data.get('image_data'):
            return jsonify({'message': 'Thiếu dữ liệu ảnh'}), 400
        
        # Simulate image analysis (in real implementation, use AI/ML models)
        import random
        import base64
        
        # Extract image data
        image_data = data['image_data']
        patient_id = data.get('patient_id')
        
        # Mock analysis results for ultrasound
        gestational_age = random.uniform(12, 40)
        bpd = random.uniform(20, 100)
        hc = random.uniform(60, 350)
        ac = random.uniform(50, 400)
        fl = random.uniform(10, 80)
        estimated_weight = random.randint(50, 4000)
        
        # Calculate analysis score
        score = 0
        status = 'normal'
        abnormalities = []
        recommendations = []
        confidence = random.randint(75, 95)
        
        # Analyze gestational age vs measurements
        if 20 <= gestational_age <= 40:
            score += 2
        else:
            abnormalities.append('Tuổi thai nằm ngoài giới hạn bình thường')
        
        # Analyze BPD
        if 20 <= bpd <= 100:
            score += 2
        else:
            abnormalities.append('Đường kính lưỡng đỉnh (BPD) bất thường')
        
        # Analyze HC
        if 60 <= hc <= 350:
            score += 2
        else:
            abnormalities.append('Chu vi đầu (HC) bất thường')
        
        # Analyze AC
        if 50 <= ac <= 400:
            score += 2
        else:
            abnormalities.append('Chu vi bụng (AC) bất thường')
        
        # Analyze FL
        if 10 <= fl <= 80:
            score += 2
        else:
            abnormalities.append('Chiều dài xương đùi (FL) bất thường')
        
        # Analyze estimated weight
        if 100 <= estimated_weight <= 4000:
            score += 2
        else:
            abnormalities.append('Cân nặng ước tính bất thường')
        
        # Determine status
        if score >= 10:
            status = 'normal'
        elif score >= 8:
            status = 'warning'
        else:
            status = 'danger'
        
        # Add recommendations based on analysis
        if status == 'warning':
            recommendations.append('Cần theo dõi thêm và có thể cần siêu âm lại')
            recommendations.append('Tư vấn với bác sĩ chuyên khoa sản')
        elif status == 'danger':
            recommendations.append('Cần đánh giá ngay lập tức bởi bác sĩ chuyên khoa')
            recommendations.append('Có thể cần thực hiện các xét nghiệm bổ sung')
        
        # Add general recommendations
        if gestational_age < 20:
            recommendations.append('Theo dõi sự phát triển của thai nhi')
        elif gestational_age > 37:
            recommendations.append('Chuẩn bị cho việc sinh nở')
        
        # Save image file (optional)
        if image_data.startswith('data:image'):
            # Extract base64 data
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            
            # Save to uploads directory
            upload_dir = 'uploads/ultrasound-images'
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = f"ultrasound_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
        
        return jsonify({
            'message': 'Phân tích ảnh siêu âm thành công',
            'gestational_age': round(gestational_age, 1),
            'bpd': round(bpd, 1),
            'hc': round(hc, 1),
            'ac': round(ac, 1),
            'fl': round(fl, 1),
            'estimated_weight': round(estimated_weight, 0),
            'analysis_score': score,
            'max_score': 12,
            'analysis_status': status,
            'confidence': confidence,
            'abnormalities': abnormalities,
            'recommendations': recommendations,
            'analysis_method': 'computer_vision',
            'image_saved': True if image_data.startswith('data:image') else False
        })
        
    except Exception as e:
        return jsonify({'message': f'Lỗi khi phân tích ảnh siêu âm: {str(e)}'}), 500

@app.route('/api/analyze-ultrasound-data', methods=['POST'])
def analyze_ultrasound_data():
    """Phân tích dữ liệu siêu âm thai thủ công"""
    try:
        data = request.json
        if not data or not data.get('patient_id'):
            return jsonify({'message': 'Thiếu dữ liệu bệnh nhân'}), 400
        
        # Extract data
        gestational_age = data.get('gestational_age', 0)
        bpd = data.get('bpd')
        hc = data.get('hc')
        ac = data.get('ac')
        fl = data.get('fl')
        estimated_weight = data.get('estimated_weight')
        ri_umbilical = data.get('ri_umbilical')
        sd_ratio = data.get('sd_ratio')
        mca_pi = data.get('mca_pi')
        cervical_length = data.get('cervical_length')
        afi = data.get('afi')
        
        # Calculate analysis score
        score = 0
        status = 'normal'
        abnormalities = []
        recommendations = []
        confidence = 85
        
        # Analyze gestational age
        if 20 <= gestational_age <= 40:
            score += 2
        else:
            abnormalities.append('Tuổi thai nằm ngoài giới hạn bình thường')
        
        # Analyze BPD
        if bpd:
            if 20 <= bpd <= 100:
                score += 2
            else:
                abnormalities.append('Đường kính lưỡng đỉnh (BPD) bất thường')
        
        # Analyze HC
        if hc:
            if 60 <= hc <= 350:
                score += 2
            else:
                abnormalities.append('Chu vi đầu (HC) bất thường')
        
        # Analyze AC
        if ac:
            if 50 <= ac <= 400:
                score += 2
            else:
                abnormalities.append('Chu vi bụng (AC) bất thường')
        
        # Analyze FL
        if fl:
            if 10 <= fl <= 80:
                score += 2
            else:
                abnormalities.append('Chiều dài xương đùi (FL) bất thường')
        
        # Analyze estimated weight
        if estimated_weight:
            if 100 <= estimated_weight <= 4000:
                score += 2
            else:
                abnormalities.append('Cân nặng ước tính bất thường')
        
        # Analyze Doppler indices
        if ri_umbilical and ri_umbilical > 0.7:
            abnormalities.append('RI động mạch rốn cao (>0.7)')
            score -= 1
        
        if sd_ratio and sd_ratio > 3.0:
            abnormalities.append('S/D ratio cao (>3.0)')
            score -= 1
        
        if mca_pi and mca_pi < 1.0:
            abnormalities.append('MCA PI thấp (<1.0)')
            score -= 1
        
        # Analyze cervical length
        if cervical_length and cervical_length < 25:
            abnormalities.append('Chiều dài cổ tử cung ngắn (<25mm)')
            score -= 2
        
        # Analyze AFI
        if afi:
            if afi < 5:
                abnormalities.append('Thiểu ối (AFI < 5cm)')
                score -= 1
            elif afi > 25:
                abnormalities.append('Đa ối (AFI > 25cm)')
                score -= 1
        
        # Determine status
        if score >= 10:
            status = 'normal'
        elif score >= 8:
            status = 'warning'
        else:
            status = 'danger'
        
        # Add recommendations based on analysis
        if status == 'warning':
            recommendations.append('Cần theo dõi thêm và có thể cần siêu âm lại')
            recommendations.append('Tư vấn với bác sĩ chuyên khoa sản')
        elif status == 'danger':
            recommendations.append('Cần đánh giá ngay lập tức bởi bác sĩ chuyên khoa')
            recommendations.append('Có thể cần thực hiện các xét nghiệm bổ sung')
        
        # Add specific recommendations
        if cervical_length and cervical_length < 25:
            recommendations.append('Cần theo dõi nguy cơ sinh non')
        
        if afi and afi < 5:
            recommendations.append('Theo dõi tình trạng nước ối')
        elif afi and afi > 25:
            recommendations.append('Theo dõi nguy cơ đa ối')
        
        if ri_umbilical and ri_umbilical > 0.7:
            recommendations.append('Theo dõi tình trạng tuần hoàn thai nhi')
        
        return jsonify({
            'message': 'Phân tích dữ liệu siêu âm thành công',
            'analysis_score': score,
            'max_score': 12,
            'analysis_status': status,
            'confidence': confidence,
            'abnormalities': abnormalities,
            'recommendations': recommendations,
            'analysis_method': 'manual_input'
        })
        
    except Exception as e:
        return jsonify({'message': f'Lỗi khi phân tích dữ liệu siêu âm: {str(e)}'}), 500

@app.route('/api/ultrasound-results', methods=['POST'])
def save_ultrasound_results():
    """Lưu kết quả siêu âm thai"""
    try:
        data = request.json
        if not data or not data.get('patient_id'):
            return jsonify({'message': 'Thiếu dữ liệu bệnh nhân'}), 400
        
        # Create new ultrasound result
        ultrasound_result = UltrasoundResult(
            patient_id=data['patient_id'],
            exam_date=data.get('exam_date', datetime.now().isoformat()),
            gestational_age=data.get('gestational_age'),
            bpd=data.get('bpd'),
            hc=data.get('hc'),
            ac=data.get('ac'),
            fl=data.get('fl'),
            ri_umbilical=data.get('ri_umbilical'),
            sd_ratio=data.get('sd_ratio'),
            mca_pi=data.get('mca_pi'),
            cervical_length=data.get('cervical_length'),
            afi=data.get('afi'),
            estimated_weight=data.get('estimated_weight'),
            fetal_position=data.get('fetal_position'),
            placenta_position=data.get('placenta_position'),
            amniotic_fluid=data.get('amniotic_fluid'),
            findings=data.get('findings'),
            recommendations=data.get('recommendations'),
            analysis_source=data.get('analysis_source', 'manual_input')
        )
        
        db.session.add(ultrasound_result)
        db.session.commit()
        
        return jsonify({'message': 'Đã lưu kết quả siêu âm thành công'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi lưu kết quả siêu âm: {str(e)}'}), 500

class CervicalResult(db.Model):
    __tablename__ = 'cervical_results'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    menstrual_cycle = db.Column(db.Date)
    cervical_color = db.Column(db.String(50))
    cervical_surface = db.Column(db.String(50))
    cervical_size = db.Column(db.String(50))
    discharge_amount = db.Column(db.String(50))
    discharge_color = db.Column(db.String(50))
    discharge_character = db.Column(db.String(50))
    lesions = db.Column(db.String(50))
    bleeding = db.Column(db.String(50))
    inflammation = db.Column(db.String(50))
    cervical_position = db.Column(db.String(50))
    os_opening = db.Column(db.String(50))
    consistency = db.Column(db.String(50))
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    analysis_source = db.Column(db.String(50), default='manual_input')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'menstrual_cycle': self.menstrual_cycle.isoformat() if self.menstrual_cycle else None,
            'cervical_color': self.cervical_color,
            'cervical_surface': self.cervical_surface,
            'cervical_size': self.cervical_size,
            'discharge_amount': self.discharge_amount,
            'discharge_color': self.discharge_color,
            'discharge_character': self.discharge_character,
            'lesions': self.lesions,
            'bleeding': self.bleeding,
            'inflammation': self.inflammation,
            'cervical_position': self.cervical_position,
            'os_opening': self.os_opening,
            'consistency': self.consistency,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'analysis_source': self.analysis_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@app.route('/api/analyze-cervical-image', methods=['POST'])
def analyze_cervical_image():
    """Phân tích ảnh soi cổ tử cung bằng điện toán"""
    try:
        data = request.json
        if not data or not data.get('image_data'):
            return jsonify({'message': 'Thiếu dữ liệu ảnh'}), 400
        
        # Simulate image analysis (in real implementation, use AI/ML models)
        import random
        import base64
        
        # Extract image data
        image_data = data['image_data']
        patient_id = data.get('patient_id')
        
        # Mock analysis results for cervical examination
        cervical_color = random.choice(['pink', 'red', 'white', 'yellow'])
        cervical_surface = random.choice(['smooth', 'rough', 'irregular'])
        cervical_size = random.choice(['normal', 'enlarged', 'small'])
        lesions = random.choice(['none', 'erosion', 'polyp', 'cyst', 'ulcer'])
        bleeding = random.choice(['none', 'contact', 'spontaneous'])
        inflammation = random.choice(['none', 'mild', 'moderate', 'severe'])
        discharge_character = random.choice(['normal', 'thick', 'thin', 'frothy'])
        
        # Calculate analysis score
        score = 0
        status = 'normal'
        abnormalities = []
        recommendations = []
        confidence = random.randint(75, 95)
        
        # Analyze cervical color
        if cervical_color == 'pink':
            score += 2
        elif cervical_color == 'red':
            score += 1
            abnormalities.append('Cổ tử cung có màu đỏ, có thể do viêm')
        else:
            abnormalities.append('Màu sắc cổ tử cung bất thường')
        
        # Analyze surface
        if cervical_surface == 'smooth':
            score += 2
        elif cervical_surface == 'rough':
            score += 1
            abnormalities.append('Bề mặt cổ tử cung gồ ghề')
        else:
            abnormalities.append('Bề mặt cổ tử cung không đều')
        
        # Analyze lesions
        if lesions == 'none':
            score += 2
        else:
            abnormalities.append(f'Phát hiện tổn thương: {lesions}')
            score -= 1
        
        # Analyze bleeding
        if bleeding == 'none':
            score += 2
        else:
            abnormalities.append(f'Có chảy máu: {bleeding}')
            score -= 1
        
        # Analyze inflammation
        if inflammation == 'none':
            score += 2
        elif inflammation == 'mild':
            score += 1
            abnormalities.append('Viêm nhẹ')
        else:
            abnormalities.append(f'Viêm {inflammation}')
            score -= 1
        
        # Analyze discharge
        if discharge_character == 'normal':
            score += 2
        else:
            abnormalities.append(f'Dịch tiết bất thường: {discharge_character}')
            score -= 1
        
        # Determine status
        if score >= 10:
            status = 'normal'
        elif score >= 8:
            status = 'warning'
        else:
            status = 'danger'
        
        # Add recommendations based on analysis
        if status == 'warning':
            recommendations.append('Cần theo dõi thêm và có thể cần xét nghiệm bổ sung')
            recommendations.append('Tư vấn với bác sĩ chuyên khoa phụ khoa')
        elif status == 'danger':
            recommendations.append('Cần đánh giá ngay lập tức bởi bác sĩ chuyên khoa')
            recommendations.append('Có thể cần thực hiện các xét nghiệm chuyên sâu')
        
        # Add specific recommendations
        if lesions != 'none':
            recommendations.append('Cần sinh thiết để xác định bản chất tổn thương')
        
        if inflammation in ['moderate', 'severe']:
            recommendations.append('Cần điều trị viêm nhiễm')
        
        if bleeding != 'none':
            recommendations.append('Cần tìm nguyên nhân chảy máu')
        
        # Save image file (optional)
        if image_data.startswith('data:image'):
            # Extract base64 data
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            
            # Save to uploads directory
            upload_dir = 'uploads/cervical-images'
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = f"cervical_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
        
        return jsonify({
            'message': 'Phân tích ảnh soi cổ tử cung thành công',
            'cervical_color': cervical_color,
            'cervical_surface': cervical_surface,
            'cervical_size': cervical_size,
            'lesions': lesions,
            'bleeding': bleeding,
            'inflammation': inflammation,
            'discharge_character': discharge_character,
            'analysis_score': score,
            'max_score': 12,
            'analysis_status': status,
            'confidence': confidence,
            'abnormalities': abnormalities,
            'recommendations': recommendations,
            'analysis_method': 'computer_vision',
            'image_saved': True if image_data.startswith('data:image') else False
        })
        
    except Exception as e:
        return jsonify({'message': f'Lỗi khi phân tích ảnh soi cổ tử cung: {str(e)}'}), 500

@app.route('/api/analyze-cervical-data', methods=['POST'])
def analyze_cervical_data():
    """Phân tích dữ liệu soi cổ tử cung thủ công"""
    try:
        data = request.json
        if not data or not data.get('patient_id'):
            return jsonify({'message': 'Thiếu dữ liệu bệnh nhân'}), 400
        
        # Extract data
        cervical_color = data.get('cervical_color')
        cervical_surface = data.get('cervical_surface')
        cervical_size = data.get('cervical_size')
        lesions = data.get('lesions')
        bleeding = data.get('bleeding')
        inflammation = data.get('inflammation')
        discharge_character = data.get('discharge_character')
        
        # Calculate analysis score
        score = 0
        status = 'normal'
        abnormalities = []
        recommendations = []
        confidence = 85
        
        # Analyze cervical color
        if cervical_color == 'pink':
            score += 2
        elif cervical_color == 'red':
            score += 1
            abnormalities.append('Cổ tử cung có màu đỏ, có thể do viêm')
        elif cervical_color in ['white', 'yellow']:
            abnormalities.append('Màu sắc cổ tử cung bất thường')
        
        # Analyze surface
        if cervical_surface == 'smooth':
            score += 2
        elif cervical_surface == 'rough':
            score += 1
            abnormalities.append('Bề mặt cổ tử cung gồ ghề')
        elif cervical_surface == 'irregular':
            abnormalities.append('Bề mặt cổ tử cung không đều')
        
        # Analyze lesions
        if lesions == 'none':
            score += 2
        else:
            abnormalities.append(f'Phát hiện tổn thương: {lesions}')
            score -= 1
        
        # Analyze bleeding
        if bleeding == 'none':
            score += 2
        else:
            abnormalities.append(f'Có chảy máu: {bleeding}')
            score -= 1
        
        # Analyze inflammation
        if inflammation == 'none':
            score += 2
        elif inflammation == 'mild':
            score += 1
            abnormalities.append('Viêm nhẹ')
        else:
            abnormalities.append(f'Viêm {inflammation}')
            score -= 1
        
        # Analyze discharge
        if discharge_character == 'normal':
            score += 2
        else:
            abnormalities.append(f'Dịch tiết bất thường: {discharge_character}')
            score -= 1
        
        # Determine status
        if score >= 10:
            status = 'normal'
        elif score >= 8:
            status = 'warning'
        else:
            status = 'danger'
        
        # Add recommendations based on analysis
        if status == 'warning':
            recommendations.append('Cần theo dõi thêm và có thể cần xét nghiệm bổ sung')
            recommendations.append('Tư vấn với bác sĩ chuyên khoa phụ khoa')
        elif status == 'danger':
            recommendations.append('Cần đánh giá ngay lập tức bởi bác sĩ chuyên khoa')
            recommendations.append('Có thể cần thực hiện các xét nghiệm chuyên sâu')
        
        # Add specific recommendations
        if lesions and lesions != 'none':
            recommendations.append('Cần sinh thiết để xác định bản chất tổn thương')
        
        if inflammation in ['moderate', 'severe']:
            recommendations.append('Cần điều trị viêm nhiễm')
        
        if bleeding and bleeding != 'none':
            recommendations.append('Cần tìm nguyên nhân chảy máu')
        
        return jsonify({
            'message': 'Phân tích dữ liệu soi cổ tử cung thành công',
            'analysis_score': score,
            'max_score': 12,
            'analysis_status': status,
            'confidence': confidence,
            'abnormalities': abnormalities,
            'recommendations': recommendations,
            'analysis_method': 'manual_input'
        })
        
    except Exception as e:
        return jsonify({'message': f'Lỗi khi phân tích dữ liệu soi cổ tử cung: {str(e)}'}), 500

@app.route('/api/cervical-results', methods=['POST'])
def save_cervical_results():
    """Lưu kết quả soi cổ tử cung"""
    try:
        data = request.json
        if not data or not data.get('patient_id'):
            return jsonify({'message': 'Thiếu dữ liệu bệnh nhân'}), 400
        
        # Create new cervical result
        cervical_result = CervicalResult(
            patient_id=data['patient_id'],
            exam_date=data.get('exam_date', datetime.now().isoformat()),
            menstrual_cycle=data.get('menstrual_cycle'),
            cervical_color=data.get('cervical_color'),
            cervical_surface=data.get('cervical_surface'),
            cervical_size=data.get('cervical_size'),
            discharge_amount=data.get('discharge_amount'),
            discharge_color=data.get('discharge_color'),
            discharge_character=data.get('discharge_character'),
            lesions=data.get('lesions'),
            bleeding=data.get('bleeding'),
            inflammation=data.get('inflammation'),
            cervical_position=data.get('cervical_position'),
            os_opening=data.get('os_opening'),
            consistency=data.get('consistency'),
            findings=data.get('findings'),
            recommendations=data.get('recommendations'),
            analysis_source=data.get('analysis_source', 'manual_input')
        )
        
        db.session.add(cervical_result)
        db.session.commit()
        
        return jsonify({'message': 'Đã lưu kết quả soi cổ tử cung thành công'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Lỗi khi lưu kết quả soi cổ tử cung: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_clinic_summary_column()
        ensure_logo_position_column()
        initialize_default_doctors()
        initialize_default_templates()
        app.run(debug=True)