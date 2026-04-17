from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET

def create_access_token(subject: str, expires_delta: int = None) -> str:
    expires = datetime.utcnow() + timedelta(seconds=(expires_delta or settings.ACCESS_TOKEN_EXPIRE_SECONDS))
    payload = {
        "sub": str(subject),
        "exp": expires,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
