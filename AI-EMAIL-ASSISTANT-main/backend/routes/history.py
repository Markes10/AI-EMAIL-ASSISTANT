from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.email import EmailRecord
from database.db import get_db
from services.pdf_exporter import export_email_to_pdf
import os
from config import config

history_bp = Blueprint("history", __name__)

# Get all emails for the logged-in user
@history_bp.route("/", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    db = next(get_db())
    emails = db.query(EmailRecord).filter(EmailRecord.user_id == user_id).order_by(EmailRecord.timestamp.desc()).all()

    history = [{
        "id": email.id,
        "subject": email.subject,
        "body": email.body,
        "tone": email.tone,
        "recipient": email.recipient,
        "timestamp": email.timestamp.isoformat()
    } for email in emails]

    return jsonify(history), 200

# Export a specific email to PDF
@history_bp.route("/export/<int:email_id>", methods=["GET"])
@jwt_required()
def export_pdf(email_id):
    user_id = get_jwt_identity()
    db = next(get_db())
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id, EmailRecord.user_id == user_id).first()

    if not email:
        return jsonify({"error": "Email not found"}), 404

    filename = f"{config.PDF_FOLDER}/email_{email.id}.pdf"
    os.makedirs(config.PDF_FOLDER, exist_ok=True)
    export_email_to_pdf(email.subject, email.body, filename)

    return send_file(filename, as_attachment=True)