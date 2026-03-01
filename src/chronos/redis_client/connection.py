import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None


async def init_redis(redis_url: str) -> aioredis.Redis:
    global _redis
    _redis = aioredis.from_url(
        redis_url,
        decode_responses=True,
        max_connections=50,
    )
    await _redis.ping()
    return _redis


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
