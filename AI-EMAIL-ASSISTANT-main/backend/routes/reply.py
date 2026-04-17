from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.generator import generate_email
from services.intent_classifier import detect_intent

reply_bp = Blueprint("reply", __name__)


@reply_bp.route("/generate", methods=["POST"])
@jwt_required()
def generate_reply():
    data = request.get_json() or {}
    original = data.get('original')
    reply_type = data.get('type', 'professional')  # short|detailed|professional
    subject = data.get('subject', 'Re: Your message')

    if not original:
        return jsonify({"error": "Original message is required"}), 400

    intent, confidence = detect_intent(original)

    # Map reply_type and intent -> tone
    tone = 'Formal'
    if reply_type == 'short':
        tone = 'Friendly' if intent in ('follow_up', 'inquiry') else 'Formal'
    elif reply_type == 'detailed':
        tone = 'Persuasive' if intent == 'job_application' else 'Formal'
    elif reply_type == 'professional':
        tone = 'Formal'

    context = (
        f"Reply to the following message (detected_intent={intent}, confidence={confidence}):\n\n{original}\n\n"
        f"Write a {reply_type} reply in a {tone.lower()} tone. Be professional and address the sender's key points."
    )

    body = generate_email(subject, context, tone)

    return jsonify({"body": body, "tone": tone, "intent": intent, "confidence": confidence}), 200
