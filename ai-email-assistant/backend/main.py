from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
from database.db import init_db
from routes.auth import auth_bp
from routes.email import email_bp
from routes.history import history_bp

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = config.JWT_SECRET
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = config.JWT_EXPIRATION

    # Enable CORS
    CORS(app)

    # Initialize JWT
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(email_bp, url_prefix="/api/email")
    app.register_blueprint(history_bp, url_prefix="/api/history")

    # Initialize DB tables (optional: run once)
    with app.app_context():
        init_db()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=config.DEBUG, host="0.0.0.0", port=5000)