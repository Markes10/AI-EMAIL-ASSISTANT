import bcrypt
from cryptography.fernet import Fernet
import os

# Load or generate Fernet key
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    # Generate a new key if not set (for dev only — store securely in prod)
    FERNET_KEY = Fernet.generate_key().decode()
    print(f"Generated new FERNET_KEY: {FERNET_KEY}")

fernet = Fernet(FERNET_KEY.encode())

# 🔐 Password hashing (bcrypt)
def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    """
    return bcrypt.checkpw(password.encode(), hashed.encode())

# 🔒 Symmetric encryption (Fernet)
def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data using Fernet.
    """
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    """
    Decrypt Fernet-encrypted data.
    """
    return fernet.decrypt(token.encode()).decode()