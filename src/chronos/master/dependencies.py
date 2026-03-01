from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chronos.db.session import get_db
from chronos.master.services.task_service import TaskService
from chronos.master.services.worker_service import WorkerService
from chronos.redis_client.connection import get_redis
from chronos.redis_client.priority_queue import PriorityQueue


async def get_task_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskService:
    redis = get_redis()
    queue = PriorityQueue(redis)
    return TaskService(session, queue)


async def get_worker_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WorkerService:
    return WorkerService(session)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
WorkerServiceDep = Annotated[WorkerService, Depends(get_worker_service)]
