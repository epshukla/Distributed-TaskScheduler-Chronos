"""Initial schema: tasks, workers, task_events tables

Revision ID: 001
Revises:
Create Date: 2026-03-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Workers table (must be created before tasks due to FK)
    op.create_table(
        "workers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hostname", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("cpu_total", sa.Float, nullable=False, server_default="4.0"),
        sa.Column("cpu_available", sa.Float, nullable=False, server_default="4.0"),
        sa.Column("memory_total", sa.Float, nullable=False, server_default="4096.0"),
        sa.Column("memory_available", sa.Float, nullable=False, server_default="4096.0"),
        sa.Column(
            "last_heartbeat",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("labels", postgresql.JSONB, server_default="{}"),
        sa.CheckConstraint(
            "status IN ('ACTIVE','DRAINING','DEAD','DEREGISTERED')",
            name="valid_worker_status",
        ),
    )
    op.create_index("idx_workers_status", "workers", ["status"])
    op.create_index("idx_workers_last_heartbeat", "workers", ["last_heartbeat"])

    # Tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("state", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("resource_cpu", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("resource_memory", sa.Float, nullable=False, server_default="256.0"),
        sa.Column(
            "assigned_worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workers.id", ondelete="SET NULL"),
        ),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("result", postgresql.JSONB),
        sa.Column("error", sa.Text),
        sa.Column("duration_seconds", sa.Float, nullable=False, server_default="10.0"),
        sa.CheckConstraint(
            "state IN ('PENDING','SCHEDULED','RUNNING','COMPLETED','FAILED','PREEMPTED','CANCELLED')",
            name="valid_task_state",
        ),
    )
    op.create_index("idx_tasks_state", "tasks", ["state"])
    op.create_index("idx_tasks_priority", "tasks", ["priority"])
    op.create_index("idx_tasks_state_priority", "tasks", ["state", "priority"])
    op.create_index("idx_tasks_assigned_worker", "tasks", ["assigned_worker_id"])
    op.create_index("idx_tasks_created_at", "tasks", ["created_at"])

    # Task events (audit log)
    op.create_table(
        "task_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_state", sa.String(20)),
        sa.Column("to_state", sa.String(20), nullable=False),
        sa.Column("worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workers.id")),
        sa.Column("reason", sa.Text),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_task_events_task_id", "task_events", ["task_id"])
    op.create_index("idx_task_events_timestamp", "task_events", ["timestamp"])


def downgrade() -> None:
    op.drop_table("task_events")
    op.drop_table("tasks")
    op.drop_table("workers")
