import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chronos.models.base import Base, TimestampMixin, UUIDMixin
from chronos.models.enums import TaskState

if TYPE_CHECKING:
    from chronos.models.worker import Worker


class Task(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "state IN ('PENDING','SCHEDULED','RUNNING','COMPLETED','FAILED','PREEMPTED','CANCELLED')",
            name="valid_task_state",
        ),
        Index("idx_tasks_state", "state"),
        Index("idx_tasks_priority", "priority"),
        Index("idx_tasks_state_priority", "state", "priority"),
        Index("idx_tasks_assigned_worker", "assigned_worker_id"),
        Index("idx_tasks_created_at", "created_at"),
    )

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    priority: Mapped[int] = mapped_column(default=0)
    state: Mapped[str] = mapped_column(String(20), default=TaskState.PENDING)

    # Resource requirements
    resource_cpu: Mapped[float] = mapped_column(default=1.0)
    resource_memory: Mapped[float] = mapped_column(default=256.0)

    # Assignment
    assigned_worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workers.id", ondelete="SET NULL"), default=None
    )

    # Retry policy
    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=3)

    # Timing
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    started_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    completed_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    # Results
    result: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)
    error: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Docker container execution
    image: Mapped[str] = mapped_column(String(512), default="alpine:latest")
    command: Mapped[Optional[list]] = mapped_column(JSONB, default=None)
    args: Mapped[Optional[list]] = mapped_column(JSONB, default=None)
    env_vars: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)
    working_dir: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=300)

    # Container execution results
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    stdout: Mapped[Optional[str]] = mapped_column(Text, default=None)
    stderr: Mapped[Optional[str]] = mapped_column(Text, default=None)
    container_id: Mapped[Optional[str]] = mapped_column(String(128), default=None)

    # Relationships
    worker: Mapped[Optional["Worker"]] = relationship(back_populates="tasks", lazy="raise")

    def __repr__(self) -> str:
        return f"<Task id={self.id} name={self.name!r} state={self.state} image={self.image!r}>"
