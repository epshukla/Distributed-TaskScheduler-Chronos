import json

import redis.asyncio as aioredis

from chronos.config.constants import worker_heartbeat_key


class HeartbeatStore:
    """Redis-based heartbeat store with TTL-based expiry for failure detection."""

    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    async def send_heartbeat(self, worker_id: str, payload: dict, ttl: int = 15) -> None:
        key = worker_heartbeat_key(worker_id)
        await self._redis.set(key, json.dumps(payload), ex=ttl)

    async def get_heartbeat(self, worker_id: str) -> dict | None:
        key = worker_heartbeat_key(worker_id)
        data = await self._redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def is_alive(self, worker_id: str) -> bool:
        key = worker_heartbeat_key(worker_id)
        return bool(await self._redis.exists(key))

    async def delete_heartbeat(self, worker_id: str) -> None:
        key = worker_heartbeat_key(worker_id)
        await self._redis.delete(key)
