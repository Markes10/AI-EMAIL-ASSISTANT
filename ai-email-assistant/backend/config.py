import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # General
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ENV = os.getenv("ENV", "development")

    # Database
    DB_URI = os.getenv("DB_URI", "sqlite:///email_history.db")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
    JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", 86400))  # in seconds

    # Hugging Face
    HF_MODEL = os.getenv("HF_MODEL", "microsoft/phi-2")
    HF_TASK = os.getenv("HF_TASK", "text-generation")

    # Email (SMTP)
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

    # PDF Export
    PDF_FOLDER = os.getenv("PDF_FOLDER", "./pdfs")

    # Tone Options
    TONE_OPTIONS = ["Formal", "Friendly", "Persuasive", "Apologetic", "Assertive"]

config = Config()