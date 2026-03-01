import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkerRegister(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    cpu_total: float = Field(default=4.0, gt=0)
    memory_total: float = Field(default=4096.0, gt=0)


class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hostname: str
    status: str
    cpu_total: float
    cpu_available: float
    memory_total: float
    memory_available: float
    last_heartbeat: datetime
    registered_at: datetime
    labels: Optional[dict]


class WorkerHeartbeat(BaseModel):
    cpu_available: float = Field(ge=0)
    memory_available: float = Field(ge=0)
