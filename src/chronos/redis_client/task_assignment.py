import redis.asyncio as aioredis

from chronos.config.constants import (
    worker_active_tasks_key,
    worker_assignments_key,
    worker_preempt_key,
)


class TaskAssignmentQueue:
    """Redis-based per-worker task assignment and preemption signaling."""

    def __init__(self, redis: aioredis.Redis):
        self._redis = redis

    # --- Assignment queue ---

    async def assign_task(self, worker_id: str, task_id: str) -> None:
        key = worker_assignments_key(worker_id)
        await self._redis.rpush(key, task_id)

    async def poll_assignment(self, worker_id: str, timeout: int = 5) -> str | None:
        key = worker_assignments_key(worker_id)
        result = await self._redis.blpop(key, timeout=timeout)
        if result is None:
            return None
        return result[1]

    # --- Preemption signals ---

    async def send_preempt_signal(self, worker_id: str, task_id: str) -> None:
        key = worker_preempt_key(worker_id)
        await self._redis.rpush(key, task_id)

    async def poll_preempt(self, worker_id: str, timeout: int = 1) -> str | None:
        key = worker_preempt_key(worker_id)
        result = await self._redis.blpop(key, timeout=timeout)
        if result is None:
            return None
        return result[1]

    async def check_preempt_nonblocking(self, worker_id: str) -> str | None:
        key = worker_preempt_key(worker_id)
        return await self._redis.lpop(key)

    # --- Active tasks tracking ---

    async def add_active_task(self, worker_id: str, task_id: str) -> None:
        key = worker_active_tasks_key(worker_id)
        await self._redis.sadd(key, task_id)

    async def remove_active_task(self, worker_id: str, task_id: str) -> None:
        key = worker_active_tasks_key(worker_id)
        await self._redis.srem(key, task_id)

    async def get_active_tasks(self, worker_id: str) -> set[str]:
        key = worker_active_tasks_key(worker_id)
        return await self._redis.smembers(key)

    async def clear_worker_data(self, worker_id: str) -> None:
        keys = [
            worker_assignments_key(worker_id),
            worker_preempt_key(worker_id),
            worker_active_tasks_key(worker_id),
        ]
        await self._redis.delete(*keys)
