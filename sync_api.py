from flask import Blueprint, request, jsonify
from app import Appointment, db

sync_bp = Blueprint("sync", __name__)

@sync_bp.route("/api/pending-appointments")
def pending_appointments():
    items = Appointment.query.filter_by(synced=False).all()

    result = []

    for a in items:
        result.append({
            "id": a.id,
            "patient_name": a.patient_name,
            "phone": a.phone,
            "exam_type": a.exam_type,
            "appointment_date": str(a.appointment_date),
            "appointment_time": str(a.appointment_time)
        })

    return jsonify(result)

@sync_bp.route("/api/mark-synced", methods=["POST"])
def mark_synced():
    ids = request.json.get("ids", [])

    for i in ids:
        item = Appointment.query.get(i)
        if item:
            item.synced = True

    db.session.commit()

    return jsonify({"success": True})