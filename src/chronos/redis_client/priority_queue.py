import redis.asyncio as aioredis

from chronos.config.constants import REDIS_TASK_QUEUE_KEY


class PriorityQueue:
    """Redis sorted-set based priority queue for task scheduling.

    Score = -priority so that ZPOPMIN returns the highest-priority task.
    """

    def __init__(self, redis: aioredis.Redis, key: str = REDIS_TASK_QUEUE_KEY):
        self._redis = redis
        self._key = key

    async def enqueue(self, task_id: str, priority: int) -> None:
        await self._redis.zadd(self._key, {task_id: -priority})

    async def dequeue(self) -> str | None:
        result = await self._redis.zpopmin(self._key, count=1)
        if not result:
            return None
        return result[0][0]

    async def dequeue_batch(self, count: int) -> list[str]:
        result = await self._redis.zpopmin(self._key, count=count)
        return [item[0] for item in result]

    async def remove(self, task_id: str) -> bool:
        removed = await self._redis.zrem(self._key, task_id)
        return removed > 0

    async def size(self) -> int:
        return await self._redis.zcard(self._key)

    async def peek(self, count: int = 10) -> list[tuple[str, float]]:
        return await self._redis.zrange(self._key, 0, count - 1, withscores=True)

    async def contains(self, task_id: str) -> bool:
        score = await self._redis.zscore(self._key, task_id)
        return score is not None

    async def clear(self) -> None:
        await self._redis.delete(self._key)
