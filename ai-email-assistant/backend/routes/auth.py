from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from models.user import User
from database.db import get_db
from utils.jwt import create_token
from utils.encryption import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)

# Register a new user
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = next(get_db())
    hashed_pw = hash_password(password)
    user = User(email=email, password_hash=hashed_pw)

    try:
        db.add(user)
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Email already exists"}), 409

# Login and get JWT token
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token(user.id)
    return jsonify({"token": token, "user_id": user.id}), 200