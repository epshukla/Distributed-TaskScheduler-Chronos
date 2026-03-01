from typing import Optional

from pydantic import BaseModel, Field

from chronos.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class HealthResponse(BaseModel):
    status: str
    is_leader: bool
    uptime_seconds: float
    node_id: str


class ReadinessResponse(BaseModel):
    status: str
    postgres: str
    redis: str
    etcd: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class PaginatedParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
