from extensions import db
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # ===== Sync giữa ONLINE (Render) và LOCAL (phòng khám) =====
    # global_id dùng để upsert giữa 2 DB khác nhau.
    global_id = db.Column(db.String(36), unique=True, index=True)
    source = db.Column(db.String(20), default='local')  # local | online
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)
    last_modified_by = db.Column(db.String(20), default='clinic')  # clinic | patient | system
    # Optional: assigned doctor for clinical forms
    doctor_name = db.Column(db.String(100), default='PK Đại Anh')
    # Optional obstetric field (yyyy-mm-dd)
    expected_delivery_date = db.Column(db.Date)
    # Ultrasound machine sync fields
    Maysieuam_synced = db.Column(db.Boolean, default=False)
    Maysieuam_sync_time = db.Column(db.DateTime)
    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))
