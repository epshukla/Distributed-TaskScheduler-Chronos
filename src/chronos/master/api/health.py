import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlalchemy import func, select

from chronos.models.enums import TaskState
from chronos.models.task import Task
from chronos.redis_client.priority_queue import PriorityQueue
from chronos.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    app = request.app
    start_time = getattr(app.state, "start_time", time.time())
    is_leader = getattr(app.state, "is_leader", False)
    node_id = getattr(app.state, "node_id", "unknown")
    return HealthResponse(
        status="healthy",
        is_leader=is_leader,
        uptime_seconds=round(time.time() - start_time, 2),
        node_id=node_id,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(request: Request) -> ReadinessResponse:
    app = request.app
    statuses = {"postgres": "unknown", "redis": "unknown", "etcd": "unknown"}

    # Check PostgreSQL
    try:
        db_factory = getattr(app.state, "db_factory", None)
        if db_factory:
            async with db_factory() as session:
                await session.execute("SELECT 1")
            statuses["postgres"] = "connected"
        else:
            statuses["postgres"] = "not_initialized"
    except Exception:
        statuses["postgres"] = "disconnected"

    # Check Redis
    try:
        redis = getattr(app.state, "redis", None)
        if redis:
            await redis.ping()
            statuses["redis"] = "connected"
        else:
            statuses["redis"] = "not_initialized"
    except Exception:
        statuses["redis"] = "disconnected"

    # Check etcd
    try:
        etcd = getattr(app.state, "etcd_client", None)
        if etcd:
            etcd.version()
            statuses["etcd"] = "connected"
        else:
            statuses["etcd"] = "not_initialized"
    except Exception:
        statuses["etcd"] = "disconnected"

    all_connected = all(v == "connected" for v in statuses.values())
    return ReadinessResponse(
        status="ready" if all_connected else "not_ready",
        **statuses,
    )


@router.get("/api/v1/stats")
async def cluster_stats(request: Request) -> dict:
    """Lightweight stats endpoint for the dashboard topology view."""
    app = request.app
    result: dict = {
        "queue_depth": 0,
        "state_counts": {},
        "worker_task_counts": {},
        "pipeline_active": 0,
    }

    # Queue depth from Redis
    try:
        redis = getattr(app.state, "redis", None)
        if redis:
            queue = PriorityQueue(redis)
            result["queue_depth"] = await queue.size()
    except Exception:
        pass

    # Task counts by state + per-worker running task counts
    try:
        db_factory = getattr(app.state, "db_factory", None)
        if db_factory:
            async with db_factory() as session:
                # State counts
                rows = await session.execute(
                    select(Task.state, func.count(Task.id)).group_by(Task.state)
                )
                result["state_counts"] = {row[0]: row[1] for row in rows}

                # Running/scheduled tasks per worker
                worker_rows = await session.execute(
                    select(Task.assigned_worker_id, func.count(Task.id))
                    .where(Task.state.in_([TaskState.RUNNING, TaskState.SCHEDULED]))
                    .where(Task.assigned_worker_id.isnot(None))
                    .group_by(Task.assigned_worker_id)
                )
                result["worker_task_counts"] = {
                    str(row[0]): row[1] for row in worker_rows
                }

                # Count tasks in active pipeline (PENDING + SCHEDULED + RUNNING)
                active_states = [TaskState.PENDING, TaskState.SCHEDULED, TaskState.RUNNING]
                active_count = await session.scalar(
                    select(func.count(Task.id)).where(Task.state.in_(active_states))
                )
                result["pipeline_active"] = active_count or 0
    except Exception:
        pass

    return result
