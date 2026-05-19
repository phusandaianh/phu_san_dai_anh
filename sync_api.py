from flask import Blueprint, request, jsonify
from models import Appointment
from extensions import db

sync_bp = Blueprint("sync", __name__)

@sync_bp.route("/api/pending-appointments")
def pending_appointments():

    items = Appointment.query.all()

    result = []

    for a in items:
        result.append({
            "id": a.id
        })

    return jsonify(result)