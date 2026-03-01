import uuid
from typing import Optional

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from chronos.master.dependencies import TaskServiceDep, WorkerServiceDep
from chronos.master.events import event_bus
from chronos.schemas.worker import WorkerHeartbeat, WorkerRegister, WorkerResponse

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])


@router.get("", response_model=list[WorkerResponse])
async def list_workers(
    service: WorkerServiceDep,
    status_filter: Optional[str] = Query(None, alias="status"),
) -> list[WorkerResponse]:
    return await service.list_workers(status=status_filter)


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: uuid.UUID, service: WorkerServiceDep) -> WorkerResponse:
    return await service.get_worker(worker_id)


# Internal endpoints for worker self-registration and heartbeat
internal_router = APIRouter(prefix="/internal/workers", tags=["internal"])


@internal_router.post("/register", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
async def register_worker(data: WorkerRegister, service: WorkerServiceDep) -> WorkerResponse:
    return await service.register_worker(data)


@internal_router.post("/{worker_id}/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def worker_heartbeat(
    worker_id: uuid.UUID,
    data: WorkerHeartbeat,
    service: WorkerServiceDep,
) -> None:
    await service.heartbeat(worker_id, data.cpu_available, data.memory_available)


# Internal task state endpoints (called by workers)

class TaskStateUpdate(BaseModel):
    state: str
    worker_id: str | None = None


class TaskCompleteRequest(BaseModel):
    result: dict | None = None
    exit_code: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    container_id: str | None = None


class TaskFailRequest(BaseModel):
    error: str
    exit_code: int | None = None
    stderr: str | None = None
    container_id: str | None = None


internal_tasks_router = APIRouter(prefix="/internal/tasks", tags=["internal"])


@internal_tasks_router.post("/{task_id}/state", status_code=status.HTTP_204_NO_CONTENT)
async def update_task_state(
    task_id: uuid.UUID,
    data: TaskStateUpdate,
    service: TaskServiceDep,
) -> None:
    from chronos.db.engine import get_session_factory
    from chronos.models.enums import TaskState
    from chronos.models.task import Task
    from chronos.state_machine.transitions import transition_task

    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            task = await session.get(Task, task_id)
            if task:
                old_state = task.state
                transition_task(task, TaskState(data.state))
                await event_bus.publish("task_state_changed", {
                    "task_id": str(task_id),
                    "name": task.name,
                    "from_state": old_state,
                    "to_state": data.state,
                    "worker_id": data.worker_id,
                    "image": task.image,
                })


@internal_tasks_router.post("/{task_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_task(
    task_id: uuid.UUID,
    data: TaskCompleteRequest,
    service: TaskServiceDep,
) -> None:
    from chronos.db.engine import get_session_factory
    from chronos.models.enums import TaskState
    from chronos.models.task import Task
    from chronos.state_machine.transitions import transition_task

    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            task = await session.get(Task, task_id)
            if task:
                old_state = task.state
                transition_task(task, TaskState.COMPLETED, result=data.result)

                # Store Docker container execution results
                if data.exit_code is not None:
                    task.exit_code = data.exit_code
                if data.stdout is not None:
                    task.stdout = data.stdout
                if data.stderr is not None:
                    task.stderr = data.stderr
                if data.container_id is not None:
                    task.container_id = data.container_id

                # Free worker resources
                if task.assigned_worker_id:
                    from chronos.models.worker import Worker
                    worker = await session.get(Worker, task.assigned_worker_id)
                    if worker:
                        worker.cpu_available += task.resource_cpu
                        worker.memory_available += task.resource_memory

                await event_bus.publish("task_state_changed", {
                    "task_id": str(task_id),
                    "name": task.name,
                    "from_state": old_state,
                    "to_state": TaskState.COMPLETED.value,
                    "worker_id": str(task.assigned_worker_id) if task.assigned_worker_id else None,
                    "exit_code": data.exit_code,
                    "image": task.image,
                })

                await event_bus.publish("container_exited", {
                    "task_id": str(task_id),
                    "name": task.name,
                    "image": task.image,
                    "exit_code": data.exit_code or 0,
                    "container_id": data.container_id or "",
                })


@internal_tasks_router.post("/{task_id}/fail", status_code=status.HTTP_204_NO_CONTENT)
async def fail_task(
    task_id: uuid.UUID,
    data: TaskFailRequest,
    service: TaskServiceDep,
) -> None:
    from chronos.db.engine import get_session_factory
    from chronos.models.enums import TaskState
    from chronos.models.task import Task
    from chronos.redis_client.connection import get_redis
    from chronos.redis_client.priority_queue import PriorityQueue
    from chronos.state_machine.transitions import transition_task

    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            task = await session.get(Task, task_id)
            if task:
                old_state = task.state
                transition_task(task, TaskState.FAILED, error=data.error)

                # Store Docker container execution results
                if data.exit_code is not None:
                    task.exit_code = data.exit_code
                if data.stderr is not None:
                    task.stderr = data.stderr
                if data.container_id is not None:
                    task.container_id = data.container_id

                # Free worker resources
                if task.assigned_worker_id:
                    from chronos.models.worker import Worker
                    worker = await session.get(Worker, task.assigned_worker_id)
                    if worker:
                        worker.cpu_available += task.resource_cpu
                        worker.memory_available += task.resource_memory

                final_state = TaskState.FAILED.value
                # Re-enqueue if retries remain
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    transition_task(task, TaskState.PENDING)
                    task.assigned_worker_id = None
                    redis = get_redis()
                    queue = PriorityQueue(redis)
                    await queue.enqueue(str(task.id), task.priority)
                    final_state = TaskState.PENDING.value

                # Detect OOM and timeout for event publishing
                is_oom = "OOM" in data.error
                is_timeout = "Timeout" in data.error

                event_type = "task_state_changed"
                if is_oom:
                    event_type = "oom_killed"
                elif is_timeout:
                    event_type = "timeout_killed"

                await event_bus.publish(event_type, {
                    "task_id": str(task_id),
                    "name": task.name,
                    "from_state": old_state,
                    "to_state": final_state,
                    "worker_id": str(task.assigned_worker_id) if task.assigned_worker_id else None,
                    "retry_count": task.retry_count,
                    "error": data.error[:500],
                    "exit_code": data.exit_code,
                    "image": task.image,
                })
