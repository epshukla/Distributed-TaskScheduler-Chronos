import uuid
from typing import Optional

from fastapi import APIRouter, Query, status

from chronos.master.dependencies import TaskServiceDep
from chronos.schemas.task import TaskCreate, TaskListResponse, TaskResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, service: TaskServiceDep) -> TaskResponse:
    return await service.create_task(data)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: uuid.UUID, service: TaskServiceDep) -> TaskResponse:
    return await service.get_task(task_id)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    service: TaskServiceDep,
    state: Optional[str] = Query(None),
    priority_min: Optional[int] = Query(None, ge=0),
    priority_max: Optional[int] = Query(None, le=100),
    worker_id: Optional[uuid.UUID] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> TaskListResponse:
    return await service.list_tasks(
        state=state,
        priority_min=priority_min,
        priority_max=priority_max,
        worker_id=worker_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.delete("/{task_id}", response_model=TaskResponse)
async def cancel_task(task_id: uuid.UUID, service: TaskServiceDep) -> TaskResponse:
    return await service.cancel_task(task_id)
