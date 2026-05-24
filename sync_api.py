from flask import Blueprint, jsonify

sync_bp = Blueprint("sync", __name__)

@sync_bp.route("/api/pending-appointments")
def pending_appointments():
    return jsonify([])