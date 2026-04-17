import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings:
    APP_NAME = os.getenv("APP_NAME", "AI Email Assistant (FastAPI)")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "ai_email_assistant")
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("JWT_EXPIRATION", 86400))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MODEL_DIR = os.getenv("MODEL_DIR", str(BASE_DIR / "models"))
    FRONTEND_OAUTH_REDIRECT_URI = os.getenv("FRONTEND_OAUTH_REDIRECT_URI", "http://localhost:3000/oauth/callback")


settings = Settings()
