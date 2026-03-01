import asyncio
import json
import uuid

from fastapi import APIRouter, Query, Request
from starlette.responses import StreamingResponse

from chronos.models.enums import TaskState
from chronos.models.task import Task

router = APIRouter(prefix="/api/v1/tasks", tags=["logs"])


@router.get("/{task_id}/logs")
async def stream_task_logs(
    task_id: uuid.UUID,
    request: Request,
    follow: bool = Query(False),
) -> StreamingResponse:
    """Stream task container logs via Server-Sent Events.

    For RUNNING tasks with follow=true: streams live Docker container logs.
    For COMPLETED/FAILED tasks: returns stored stdout/stderr from the database.
    """
    app = request.app
    db_factory = getattr(app.state, "db_factory", None)

    if not db_factory:
        return StreamingResponse(
            _sse_error("Database not initialized"),
            media_type="text/event-stream",
        )

    # Fetch the task
    async with db_factory() as session:
        task = await session.get(Task, task_id)
        if task is None:
            return StreamingResponse(
                _sse_error("Task not found"),
                media_type="text/event-stream",
            )

        task_state = task.state
        task_stdout = task.stdout or ""
        task_stderr = task.stderr or ""
        task_container_id = task.container_id
        task_image = task.image

    # For completed/failed tasks, return stored logs
    if task_state in (
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.CANCELLED,
    ):
        return StreamingResponse(
            _sse_stored_logs(task_stdout, task_stderr, task_state),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # For running tasks, try to stream live logs from Docker
    if task_state == TaskState.RUNNING and follow and task_container_id:
        return StreamingResponse(
            _sse_live_logs(task_container_id, task_id, db_factory),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # For other states (PENDING, SCHEDULED), no logs yet
    return StreamingResponse(
        _sse_no_logs(task_state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _sse_stored_logs(stdout: str, stderr: str, state: str):
    """Yield stored logs as SSE events."""
    if stdout:
        for line in stdout.split("\n"):
            yield f"data: {json.dumps({'stream': 'stdout', 'line': line})}\n\n"
    if stderr:
        for line in stderr.split("\n"):
            yield f"data: {json.dumps({'stream': 'stderr', 'line': line})}\n\n"
    yield f"data: {json.dumps({'stream': 'system', 'line': f'Task {state}'})}\n\n"
    yield "event: done\ndata: {}\n\n"


async def _sse_live_logs(container_id: str, task_id: uuid.UUID, db_factory):
    """Stream live container logs via Docker SDK."""
    import docker
    import docker.errors

    try:
        client = docker.from_env()
        container = client.containers.get(container_id)

        # Stream logs
        for chunk in container.logs(stream=True, follow=True, timestamps=False):
            line = chunk.decode("utf-8", errors="replace").rstrip("\n")
            yield f"data: {json.dumps({'stream': 'stdout', 'line': line})}\n\n"

        # Container exited — send final state
        container.reload()
        exit_code = container.attrs.get("State", {}).get("ExitCode", -1)
        yield f"data: {json.dumps({'stream': 'system', 'line': f'Container exited with code {exit_code}'})}\n\n"

    except docker.errors.NotFound:
        # Container already removed — fall back to stored logs
        async with db_factory() as session:
            task = await session.get(Task, task_id)
            if task and task.stdout:
                for line in task.stdout.split("\n"):
                    yield f"data: {json.dumps({'stream': 'stdout', 'line': line})}\n\n"
            if task and task.stderr:
                for line in task.stderr.split("\n"):
                    yield f"data: {json.dumps({'stream': 'stderr', 'line': line})}\n\n"
        yield f"data: {json.dumps({'stream': 'system', 'line': 'Container no longer exists'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'stream': 'system', 'line': f'Log stream error: {e}'})}\n\n"

    yield "event: done\ndata: {}\n\n"


async def _sse_no_logs(state: str):
    """Yield a message indicating no logs are available yet."""
    yield f"data: {json.dumps({'stream': 'system', 'line': f'Task is {state} — no logs yet'})}\n\n"
    yield "event: done\ndata: {}\n\n"


async def _sse_error(message: str):
    """Yield an error message as SSE."""
    yield f"data: {json.dumps({'stream': 'system', 'line': f'Error: {message}'})}\n\n"
    yield "event: done\ndata: {}\n\n"
