import jwt
import datetime
from config import config

def create_token(user_id: int) -> str:
    """
    Create a JWT token for the given user ID.

    Args:
        user_id (int): Unique identifier for the user.

    Returns:
        str: Encoded JWT token.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=config.JWT_EXPIRATION),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    """
    Decode a JWT token and return its payload.

    Args:
        token (str): Encoded JWT token.

    Returns:
        dict: Decoded payload if valid.

    Raises:
        jwt.ExpiredSignatureError: If token is expired.
        jwt.InvalidTokenError: If token is malformed or invalid.
    """
    return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])