from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.tone_adapter import adjust_tone, analyze_tone, normalize_tone

tone_bp = Blueprint("tone", __name__)


@tone_bp.route("/adjust", methods=["POST"])
@jwt_required()
def adjust():
    data = request.get_json() or {}
    text = data.get('text')
    target_tone = data.get('target_tone')

    if not text or not target_tone:
        return jsonify({"error": "Both 'text' and 'target_tone' are required"}), 400

    try:
        adjusted = adjust_tone(text, target_tone)
        detected, confidence = analyze_tone(text)
        return jsonify({
            "original_tone": detected,
            "original_confidence": confidence,
            "target_tone": normalize_tone(target_tone),
            "adjusted_text": adjusted
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
