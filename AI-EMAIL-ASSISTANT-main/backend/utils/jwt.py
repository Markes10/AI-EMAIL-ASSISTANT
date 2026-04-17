from config import config
from datetime import datetime, timedelta
try:
    # Prefer using flask_jwt_extended's helper when available so tokens
    # are compatible with jwt_required() and get_jwt_identity().
    from flask_jwt_extended import create_access_token
    FLASK_JWT_AVAILABLE = True
except Exception:
    import jwt as _pyjwt
    FLASK_JWT_AVAILABLE = False


def create_token(user_id: int) -> str:
    """
    Create an access token for the given user ID.

    Uses `flask_jwt_extended.create_access_token` when available. Falls back
    to a PyJWT token if not.
    """
    if FLASK_JWT_AVAILABLE:
        # create_access_token will use the Flask app's JWT settings
        return create_access_token(identity=user_id, expires_delta=timedelta(seconds=config.JWT_EXPIRATION))

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(seconds=config.JWT_EXPIRATION),
        "iat": datetime.utcnow()
    }
    return _pyjwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    Decode a token using PyJWT as a fallback. When using flask_jwt_extended,
    prefer that library's mechanisms instead of calling this function.
    """
    if FLASK_JWT_AVAILABLE:
        # Let flask_jwt_extended handle decode flows in app context
        try:
            from flask_jwt_extended import decode_token as _fjw_decode
            return _fjw_decode(token)
        except Exception:
            pass

    return _pyjwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])