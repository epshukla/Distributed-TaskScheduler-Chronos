from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from redis.asyncio.lock import Lock


class DistributedLock:
    """Redis-based distributed lock using RedLock pattern (single-instance)."""

    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    @asynccontextmanager
    async def lock(
        self,
        name: str,
        timeout: float = 10.0,
        blocking_timeout: float = 5.0,
    ) -> AsyncGenerator[Lock, None]:
        lock = self._redis.lock(
            name,
            timeout=timeout,
            blocking_timeout=blocking_timeout,
        )
        acquired = await lock.acquire()
        if not acquired:
            raise TimeoutError(f"Could not acquire lock: {name}")
        try:
            yield lock
        finally:
            try:
                await lock.release()
            except Exception:
                pass  # lock may have expired
