import hashlib
import time
import redis.asyncio as aioredis
from app.config import settings
from fastapi import HTTPException

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def is_allowed(key: str, limit: int = 10, period: int = 60, identifier: str = None) -> bool:
    """Simple token-bucket per-identifier rate limiter backed by Redis.

    key: logical key for the endpoint (e.g., 'generate_email')
    identifier: usually client IP or user id
    """
    r = await get_redis()
    id_part = identifier or 'anon'
    redis_key = f"rl:{key}:{id_part}"
    try:
        current = await r.incr(redis_key)
        if current == 1:
            await r.expire(redis_key, period)
        if current > limit:
            return False
        return True
    except Exception:
        # In case of Redis errors, allow through (fail-open)
        return True


async def ensure_allowed_or_429(key: str, limit: int = 10, period: int = 60, identifier: str = None):
    ok = await is_allowed(key, limit=limit, period=period, identifier=identifier)
    if not ok:
        raise HTTPException(status_code=429, detail='Too many requests')
