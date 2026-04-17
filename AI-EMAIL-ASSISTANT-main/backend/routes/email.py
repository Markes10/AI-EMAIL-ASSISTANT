from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.email import EmailRecord
from database.db import get_db
from services.generator import generate_email
from services.sender import send_email
from config import config
from werkzeug.utils import secure_filename
import os
from datetime import datetime

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
    # Support both JSON and multipart/form-data (attachments)
    recipient = None
    subject = None
    body = None
    cc = None
    bcc = None
    saved_paths = []

    try:
        if request.content_type and request.content_type.startswith("multipart/form-data"):
            recipient = request.form.get("recipient")
            subject = request.form.get("subject")
            body = request.form.get("body")
            cc = request.form.get("cc")
            bcc = request.form.get("bcc")

            # Handle files
            files = request.files.getlist("attachments")
            upload_folder = getattr(config, "UPLOAD_FOLDER", config.PDF_FOLDER)
            os.makedirs(upload_folder, exist_ok=True)
            for f in files:
                if f and f.filename:
                    filename = secure_filename(f.filename)
                    timestamp = int(datetime.utcnow().timestamp() * 1000)
                    save_name = f"{timestamp}_{filename}"
                    save_path = os.path.join(upload_folder, save_name)
                    f.save(save_path)
                    saved_paths.append(save_path)
        else:
            data = request.get_json() or {}
            recipient = data.get("recipient")
            subject = data.get("subject")
            body = data.get("body")
            cc = data.get("cc")
            bcc = data.get("bcc")

        if not recipient or not subject or not body:
            return jsonify({"error": "Recipient, subject, and body are required"}), 400

        # Send the email
        send_email(
            sender=config.EMAIL_SENDER,
            password=config.EMAIL_PASSWORD,
            recipient=recipient,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            attachments=saved_paths
        )

        # Save to DB
        db = next(get_db())
        email_record = EmailRecord(
            subject=subject,
            body=body,
            tone=None,
            recipient=recipient,
            user_id=get_jwt_identity()
        )
        db.add(email_record)
        db.commit()

        # Cleanup saved files
        for p in saved_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        # Cleanup on error
        for p in saved_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500