from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.email import EmailRecord
from database.db import get_db
from services.generator import generate_email
from services.sender import send_email
from config import config

email_bp = Blueprint("email", __name__)

# Generate email content
@email_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate():
    data = request.get_json()
    subject = data.get("subject")
    context = data.get("context")
    tone = data.get("tone", "Formal")

    if not subject or not context:
        return jsonify({"error": "Subject and context are required"}), 400

    user_id = get_jwt_identity()
    body = generate_email(subject, context, tone)

    # Save to DB
    db = next(get_db())
    email_record = EmailRecord(
        subject=subject,
        body=body,
        tone=tone,
        user_id=user_id
    )
    db.add(email_record)
    db.commit()

    return jsonify({
        "subject": subject,
        "body": body,
        "tone": tone,
        "email_id": email_record.id
    }), 200

# Send email via SMTP
@email_bp.route("/send", methods=["POST"])
@jwt_required()
def send():
    data = request.get_json()
    recipient = data.get("recipient")
    subject = data.get("subject")
    body = data.get("body")

    if not recipient or not subject or not body:
        return jsonify({"error": "Recipient, subject, and body are required"}), 400

    try:
        send_email(
            sender=config.EMAIL_SENDER,
            password=config.EMAIL_PASSWORD,
            recipient=recipient,
            subject=subject,
            body=body
        )
        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500