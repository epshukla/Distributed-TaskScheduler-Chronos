import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=100)
    resource_cpu: float = Field(default=1.0, gt=0, le=64.0)
    resource_memory: float = Field(default=256.0, gt=0, le=65536.0)
    max_retries: int = Field(default=3, ge=0, le=10)

    # Docker container execution
    image: str = Field(..., min_length=1, max_length=512)
    command: Optional[list[str]] = None
    args: Optional[list[str]] = None
    env_vars: Optional[dict[str, str]] = None
    working_dir: Optional[str] = None
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: Optional[str]
    priority: int
    state: str
    resource_cpu: float
    resource_memory: float
    assigned_worker_id: Optional[uuid.UUID]
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[dict]
    error: Optional[str]

    # Docker container execution
    image: str
    command: Optional[list[str]]
    args: Optional[list[str]]
    env_vars: Optional[dict[str, str]]
    working_dir: Optional[str]
    timeout_seconds: int
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    container_id: Optional[str]


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    pages: int
