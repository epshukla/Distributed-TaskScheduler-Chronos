"""Add Docker container execution fields to tasks table

Revision ID: 002
Revises: 001
Create Date: 2026-03-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Docker execution input fields
    op.add_column("tasks", sa.Column("image", sa.String(512), nullable=False, server_default="alpine:latest"))
    op.add_column("tasks", sa.Column("command", sa.JSON, nullable=True))
    op.add_column("tasks", sa.Column("args", sa.JSON, nullable=True))
    op.add_column("tasks", sa.Column("env_vars", sa.JSON, nullable=True))
    op.add_column("tasks", sa.Column("working_dir", sa.String(512), nullable=True))
    op.add_column("tasks", sa.Column("timeout_seconds", sa.Integer, nullable=False, server_default="300"))

    # Docker execution result fields
    op.add_column("tasks", sa.Column("exit_code", sa.Integer, nullable=True))
    op.add_column("tasks", sa.Column("stdout", sa.Text, nullable=True))
    op.add_column("tasks", sa.Column("stderr", sa.Text, nullable=True))
    op.add_column("tasks", sa.Column("container_id", sa.String(128), nullable=True))

    # Remove old simulation field
    op.drop_column("tasks", "duration_seconds")


def downgrade() -> None:
    op.add_column("tasks", sa.Column("duration_seconds", sa.Float, nullable=False, server_default="10.0"))
    op.drop_column("tasks", "container_id")
    op.drop_column("tasks", "stderr")
    op.drop_column("tasks", "stdout")
    op.drop_column("tasks", "exit_code")
    op.drop_column("tasks", "timeout_seconds")
    op.drop_column("tasks", "working_dir")
    op.drop_column("tasks", "env_vars")
    op.drop_column("tasks", "args")
    op.drop_column("tasks", "command")
    op.drop_column("tasks", "image")
