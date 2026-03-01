from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from chronos.models.base import Base, TimestampMixin, UUIDMixin
from chronos.models.enums import WorkerStatus

if TYPE_CHECKING:
    from chronos.models.task import Task


class Worker(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE','DRAINING','DEAD','DEREGISTERED')",
            name="valid_worker_status",
        ),
        Index("idx_workers_status", "status"),
        Index("idx_workers_last_heartbeat", "last_heartbeat"),
    )

    hostname: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(20), default=WorkerStatus.ACTIVE)

    # Total resources
    cpu_total: Mapped[float] = mapped_column(default=4.0)
    cpu_available: Mapped[float] = mapped_column(default=4.0)
    memory_total: Mapped[float] = mapped_column(default=4096.0)
    memory_available: Mapped[float] = mapped_column(default=4096.0)

    # Timing
    last_heartbeat: Mapped[datetime] = mapped_column(server_default=func.now())
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Metadata
    labels: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(back_populates="worker", lazy="raise")

    def __repr__(self) -> str:
        return (
            f"<Worker id={self.id} hostname={self.hostname!r} status={self.status} "
            f"cpu={self.cpu_available}/{self.cpu_total} mem={self.memory_available}/{self.memory_total}>"
        )
