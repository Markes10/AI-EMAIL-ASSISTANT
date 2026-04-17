from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from database.db import get_db
from models.resume import Resume
from services.resume_matcher import compute_match_score
from config import config
import os

resume_bp = Blueprint("resume", __name__)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@resume_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)
    upload_folder = getattr(config, "UPLOAD_FOLDER", "./uploads")
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, f"{get_jwt_identity()}_{filename}")
    file.save(save_path)

    # Try to extract text content (basic support)
    content = ""
    ext = filename.rsplit('.', 1)[1].lower()
    try:
        if ext == 'pdf':
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(save_path)
                pages = [p.extract_text() or "" for p in reader.pages]
                content = "\n".join(pages)
            except Exception:
                content = ""
        elif ext in ('doc', 'docx'):
            try:
                import docx
                doc = docx.Document(save_path)
                content = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                content = ""
        else:
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
    except Exception:
        content = ""

    # Save resume record
    db = next(get_db())
    resume = Resume(filename=filename, content=content, user_id=get_jwt_identity())
    db.add(resume)
    db.commit()

    return jsonify({"resume_id": resume.id, "filename": filename}), 201


@resume_bp.route("/match", methods=["POST"])
@jwt_required()
def match_resume():
    data = request.get_json() or {}
    job_description = data.get('jobDescription')
    resume_id = data.get('resumeId')

    if not job_description:
        return jsonify({"error": "jobDescription is required"}), 400

    db = next(get_db())
    if resume_id:
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == get_jwt_identity()).first()
        if not resume:
            return jsonify({"error": "Resume not found"}), 404
        resume_text = resume.content
    else:
        resume = db.query(Resume).filter(Resume.user_id == get_jwt_identity()).order_by(Resume.uploaded_at.desc()).first()
        if not resume:
            return jsonify({"error": "No resume found for user"}), 404
        resume_text = resume.content

    overall_score, detailed_scores = compute_match_score(resume_text, job_description)
    resume.matched_score = int(overall_score)
    db.add(resume)
    db.commit()

    return jsonify({"match_score": int(overall_score), "detailed_scores": detailed_scores}), 200


@resume_bp.route("/list", methods=["GET"])
@jwt_required()
def list_resumes():
    db = next(get_db())
    resumes = db.query(Resume).filter(Resume.user_id == get_jwt_identity()).order_by(Resume.uploaded_at.desc()).all()
    result = [
        {"id": r.id, "filename": r.filename, "uploaded_at": r.uploaded_at.isoformat(), "matched_score": r.matched_score}
        for r in resumes
    ]
    return jsonify(result), 200
