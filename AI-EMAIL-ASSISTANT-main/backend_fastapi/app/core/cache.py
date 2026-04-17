import redis.asyncio as aioredis
from app.config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def cache_get(key: str):
    r = await get_redis()
    try:
        return await r.get(key)
    except Exception:
        return None

async def cache_set(key: str, value: str, expire: int = 300):
    r = await get_redis()
    try:
        await r.set(key, value, ex=expire)
    except Exception:
        pass
