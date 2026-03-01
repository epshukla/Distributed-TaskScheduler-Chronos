import uuid
from math import ceil

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronos.exceptions import InvalidStateTransitionError, TaskNotFoundError
from chronos.metrics.instrumentator import record_state_transition, record_task_submitted
from chronos.models.enums import TaskState
from chronos.models.task import Task
from chronos.redis_client.priority_queue import PriorityQueue
from chronos.master.events import event_bus
from chronos.schemas.task import TaskCreate, TaskListResponse, TaskResponse
from chronos.state_machine.transitions import transition_task

logger = structlog.get_logger(__name__)


class TaskService:
    def __init__(self, session: AsyncSession, priority_queue: PriorityQueue):
        self._session = session
        self._queue = priority_queue

    async def create_task(self, data: TaskCreate) -> TaskResponse:
        task = Task(
            id=uuid.uuid4(),
            name=data.name,
            description=data.description,
            priority=data.priority,
            state=TaskState.PENDING,
            resource_cpu=data.resource_cpu,
            resource_memory=data.resource_memory,
            max_retries=data.max_retries,
            image=data.image,
            command=data.command,
            args=data.args,
            env_vars=data.env_vars,
            working_dir=data.working_dir,
            timeout_seconds=data.timeout_seconds,
        )
        self._session.add(task)
        await self._session.flush()

        # Enqueue to Redis priority queue
        await self._queue.enqueue(str(task.id), task.priority)

        record_task_submitted(task.priority)
        logger.info(
            "task_created",
            task_id=str(task.id),
            name=task.name,
            priority=task.priority,
            image=task.image,
        )

        await event_bus.publish("task_created", {
            "task_id": str(task.id),
            "name": task.name,
            "priority": task.priority,
            "state": task.state,
            "resource_cpu": task.resource_cpu,
            "resource_memory": task.resource_memory,
            "image": task.image,
        })

        return TaskResponse.model_validate(task)

    async def get_task(self, task_id: uuid.UUID) -> TaskResponse:
        task = await self._session.get(Task, task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))
        return TaskResponse.model_validate(task)

    async def list_tasks(
        self,
        state: str | None = None,
        priority_min: int | None = None,
        priority_max: int | None = None,
        worker_id: uuid.UUID | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> TaskListResponse:
        query = select(Task)
        count_query = select(func.count(Task.id))

        if state:
            query = query.where(Task.state == state)
            count_query = count_query.where(Task.state == state)
        if priority_min is not None:
            query = query.where(Task.priority >= priority_min)
            count_query = count_query.where(Task.priority >= priority_min)
        if priority_max is not None:
            query = query.where(Task.priority <= priority_max)
            count_query = count_query.where(Task.priority <= priority_max)
        if worker_id:
            query = query.where(Task.assigned_worker_id == worker_id)
            count_query = count_query.where(Task.assigned_worker_id == worker_id)

        # Sorting
        sort_column = getattr(Task, sort_by, Task.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Count
        total = await self._session.scalar(count_query) or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self._session.execute(query)
        tasks = list(result.scalars().all())

        return TaskListResponse(
            items=[TaskResponse.model_validate(t) for t in tasks],
            total=total,
            page=page,
            page_size=page_size,
            pages=ceil(total / page_size) if page_size > 0 else 0,
        )

    async def cancel_task(self, task_id: uuid.UUID) -> TaskResponse:
        task = await self._session.get(Task, task_id)
        if task is None:
            raise TaskNotFoundError(str(task_id))

        current_state = TaskState(task.state)
        if current_state in (TaskState.COMPLETED, TaskState.CANCELLED):
            raise InvalidStateTransitionError(current_state.value, TaskState.CANCELLED.value)

        old_state = task.state
        transition_task(task, TaskState.CANCELLED)
        task.assigned_worker_id = None

        # Remove from queue if pending
        if current_state == TaskState.PENDING:
            await self._queue.remove(str(task.id))

        record_state_transition(old_state, TaskState.CANCELLED)
        logger.info("task_cancelled", task_id=str(task_id), from_state=old_state)

        await event_bus.publish("task_state_changed", {
            "task_id": str(task_id),
            "name": task.name,
            "from_state": old_state,
            "to_state": TaskState.CANCELLED.value,
        })

        return TaskResponse.model_validate(task)
