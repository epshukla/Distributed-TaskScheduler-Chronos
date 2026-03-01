import asyncio
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chronos.models.base import Base
from chronos.models.enums import TaskState, WorkerStatus
from chronos.models.task import Task
from chronos.models.worker import Worker
from chronos.redis_client.priority_queue import PriorityQueue


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.zadd = AsyncMock()
    redis.zpopmin = AsyncMock(return_value=[])
    redis.zrem = AsyncMock(return_value=1)
    redis.zcard = AsyncMock(return_value=0)
    redis.zrange = AsyncMock(return_value=[])
    redis.zscore = AsyncMock(return_value=None)
    redis.delete = AsyncMock()
    redis.set = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.exists = AsyncMock(return_value=0)
    redis.rpush = AsyncMock()
    redis.blpop = AsyncMock(return_value=None)
    redis.lpop = AsyncMock(return_value=None)
    redis.sadd = AsyncMock()
    redis.srem = AsyncMock()
    redis.smembers = AsyncMock(return_value=set())
    redis.lock = MagicMock()
    redis.ping = AsyncMock()
    return redis


@pytest.fixture
def mock_priority_queue(mock_redis):
    return PriorityQueue(mock_redis)


@pytest.fixture
def sample_task() -> Task:
    return Task(
        id=uuid.uuid4(),
        name="test-task",
        description="A test task",
        priority=50,
        state=TaskState.PENDING,
        resource_cpu=2.0,
        resource_memory=512.0,
        max_retries=3,
        duration_seconds=10.0,
    )


@pytest.fixture
def sample_worker() -> Worker:
    return Worker(
        id=uuid.uuid4(),
        hostname="test-worker-1",
        status=WorkerStatus.ACTIVE,
        cpu_total=4.0,
        cpu_available=4.0,
        memory_total=4096.0,
        memory_available=4096.0,
    )
