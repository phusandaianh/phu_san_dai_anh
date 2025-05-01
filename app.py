from flask import Flask, render_template, send_from_directory, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
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
    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # 'kham', 'can-lam-sang'

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    patient = db.relationship('Patient', backref=db.backref('medical_records', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('medical_record', lazy=True))

class ClinicalService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointment = db.relationship('Appointment', backref=db.backref('clinical_services', lazy=True))
    service = db.relationship('Service', backref=db.backref('clinical_services', lazy=True))

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
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
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
    schedule = db.Column(db.Text)
    contact = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorkSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # yyyy-mm-dd
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    doctor_name = db.Column(db.String(100), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
            return jsonify({'message': f'Thông tin "{field}" không được để trống.'}), 400
    # Kiểm tra số điện thoại hợp lệ (10-11 số, chỉ chứa số)
    if not re.match(r'^\d{10,11}$', data['phone']):
        return jsonify({'message': 'Số điện thoại không hợp lệ. Vui lòng nhập đúng 10-11 số.'}), 400
    # Kiểm tra ngày sinh hợp lệ
    try:
        dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d')
    except Exception:
        return jsonify({'message': 'Ngày sinh không hợp lệ. Định dạng đúng: yyyy-mm-dd.'}), 400
    try:
        patient = Patient(
            name=data['name'],
            phone=data['phone'],
            address=data.get('address'),
            date_of_birth=dob
        )
        db.session.add(patient)
        db.session.commit()

        appointment = Appointment(
            patient_id=patient.id,
            appointment_date=datetime.now(),
            service_type=data['service_type']
        )
        db.session.add(appointment)
        db.session.commit()

        return jsonify({'message': 'Appointment created successfully', 'appointment_id': appointment.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Đã xảy ra lỗi hệ thống: {str(e)}'}), 500

@app.route('/api/services', methods=['GET'])
def get_services():
    services = Service.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'price': s.price,
        'description': s.description
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
    today = datetime.now().date()
    appointments = Appointment.query.filter(
        db.func.date(Appointment.appointment_date) == today
    ).order_by(Appointment.appointment_date).all()
    
    return jsonify([{
        'id': a.id,
        'patient_name': a.patient.name,
        'patient_phone': a.patient.phone,
        'appointment_date': a.appointment_date.isoformat(),
        'service_type': a.service_type,
        'status': a.status
    } for a in appointments])

@app.route('/api/clinical-services', methods=['GET'])
def get_clinical_services():
    services = ClinicalServiceSetting.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'price': s.price
    } for s in services])

@app.route('/api/clinical-services', methods=['POST'])
def create_clinical_service():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    if not name or not description or price is None:
        return jsonify({'message': 'Vui lòng nhập đầy đủ thông tin dịch vụ.'}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({'message': 'Giá dịch vụ không hợp lệ.'}), 400
    service = ClinicalServiceSetting(name=name, description=description, price=price)
    db.session.add(service)
    db.session.commit()
    return jsonify({'message': 'Đã thêm dịch vụ cận lâm sàng thành công!', 'id': service.id})

@app.route('/api/clinical-services/<int:id>', methods=['PUT'])
def update_clinical_service(id):
    data = request.json
    service = ClinicalServiceSetting.query.get_or_404(id)
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    if not name or not description or price is None:
        return jsonify({'message': 'Vui lòng nhập đầy đủ thông tin dịch vụ.'}), 400
    try:
        price = float(price)
    except Exception:
        return jsonify({'message': 'Giá dịch vụ không hợp lệ.'}), 400
    service.name = name
    service.description = description
    service.price = price
    db.session.commit()
    return jsonify({'message': 'Đã cập nhật dịch vụ thành công!'})

@app.route('/api/clinical-services/<int:id>', methods=['DELETE'])
def delete_clinical_service(id):
    service = ClinicalServiceSetting.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Đã xóa dịch vụ thành công!'})

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
        'services': [{
            'name': s.name,
            'description': s.description
        } for s in services],
        'contactInfo': [{
            'type': c.type,
            'value': c.value
        } for c in contact_info]
    })

@app.route('/api/home-content', methods=['POST'])
def update_home_content():
    data = request.json
    
    # Update home content
    home_content = HomeContent.query.first()
    if not home_content:
        home_content = HomeContent()
        db.session.add(home_content)
    
    home_content.hero_title = data['heroTitle']
    home_content.hero_description = data['heroDescription']
    
    # Update services
    Service.query.delete()  # Clear existing services
    for service in data['services']:
        new_service = Service(
            name=service['name'],
            description=service['description']
        )
        db.session.add(new_service)
    
    # Update contact info
    ContactInfo.query.delete()  # Clear existing contact info
    for contact in data['contactInfo']:
        new_contact = ContactInfo(
            type=contact['type'],
            value=contact['value']
        )
        db.session.add(new_contact)
    
    db.session.commit()
    return jsonify({'message': 'Nội dung trang chủ đã được cập nhật'})

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
            'description': s.description,
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
    test_result = TestResult.query.get_or_404(id)
    # Xóa file nếu có
    if test_result.file_path and os.path.exists(test_result.file_path):
        os.remove(test_result.file_path)
    db.session.delete(test_result)
    db.session.commit()
    return jsonify({'message': 'Đã xóa kết quả!'})

# API: Trả file upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/booking-content', methods=['GET'])
def get_booking_content():
    content = BookingPageContent.query.first()
    if not content:
        # Nội dung mặc định nếu chưa có
        content = BookingPageContent(
            title='Đặt lịch khám trực tuyến',
            description='Đăng ký khám nhanh chóng, chủ động chọn thời gian, tiết kiệm thời gian chờ đợi tại phòng khám.',
            services='["Khám thai định kỳ","Siêu âm 2D, 4D, 5D","Xét nghiệm máu, nước tiểu","Tiêm phòng uốn ván, cúm","Tư vấn tiền sản"]',
            utilities='["Dinh dưỡng thai kỳ","Bài tập cho bà bầu","Địa chỉ mua sắm","Hỏi đáp"]',
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
        'schedule': content.schedule,
        'contact': content.contact
    })

@app.route('/api/booking-content', methods=['POST'])
def update_booking_content():
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
    content.schedule = data.get('schedule', content.schedule)
    content.contact = data.get('contact', content.contact)
    db.session.commit()
    return jsonify({'message': 'Đã cập nhật nội dung trang đặt lịch khám!'})

@app.route('/api/work-schedule', methods=['GET'])
def get_work_schedule():
    # Dữ liệu mẫu: 14 ngày tới, mỗi ngày 1-3 ca khám, mỗi ca 1 bác sĩ
    today = datetime.now().date()
    schedule = []
    for i in range(14):
        date = today + timedelta(days=i)
        shifts = []
        # Ví dụ: Thứ 7, CN chỉ 1 ca, ngày thường 2-3 ca
        weekday = date.weekday()
        if weekday == 5:  # Thứ 7
            shifts.append({
                'start_time': '16:30',
                'end_time': '20:00',
                'doctor_name': 'Ths - Bs Quỳnh Anh'
            })
        elif weekday == 6:  # Chủ nhật nghỉ
            shifts = []
        else:
            shifts.append({
                'start_time': '16:30',
                'end_time': '18:00',
                'doctor_name': 'Ths - Bs Quỳnh Anh'
            })
            shifts.append({
                'start_time': '18:00',
                'end_time': '20:00',
                'doctor_name': 'Bs Nguyễn Văn A'
            })
            if weekday % 2 == 0:
                shifts.append({
                    'start_time': '17:00',
                    'end_time': '19:00',
                    'doctor_name': 'Bs Lê Thị B'
                })
        schedule.append({
            'date': date.strftime('%Y-%m-%d'),
            'shifts': shifts
        })
    return jsonify(schedule)

@app.route('/api/admin/work-schedule', methods=['GET'])
def admin_get_work_schedule():
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
            'doctor_name': s.doctor_name
        } for s in schedules
    ])

@app.route('/api/admin/work-schedule', methods=['POST'])
def admin_add_work_schedule():
    data = request.json
    ws = WorkSchedule(
        date=data['date'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        doctor_name=data['doctor_name']
    )
    db.session.add(ws)
    db.session.commit()
    return jsonify({'message': 'Đã thêm ca khám!', 'id': ws.id})

@app.route('/api/admin/work-schedule/<int:id>', methods=['PUT'])
def admin_update_work_schedule(id):
    ws = WorkSchedule.query.get_or_404(id)
    data = request.json
    ws.date = data.get('date', ws.date)
    ws.start_time = data.get('start_time', ws.start_time)
    ws.end_time = data.get('end_time', ws.end_time)
    ws.doctor_name = data.get('doctor_name', ws.doctor_name)
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)