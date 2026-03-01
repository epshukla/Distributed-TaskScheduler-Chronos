import asyncio
import random

import structlog

logger = structlog.get_logger(__name__)


class TaskPreemptedError(Exception):
    pass


class TaskExecutionError(Exception):
    pass


async def run_task(
    task_id: str,
    task_data: dict,
    cancel_event: asyncio.Event,
) -> dict:
    """Simulate task execution.

    Sleeps for duration_seconds while periodically checking for preemption.
    Simulates ~5% random failure rate for realistic testing.
    """
    duration = task_data.get("duration_seconds", 10.0)
    name = task_data.get("name", "unknown")

    logger.info("task_execution_started", task_id=task_id, name=name, duration=duration)

    elapsed = 0.0
    check_interval = 0.5  # check for preemption every 500ms

    while elapsed < duration:
        if cancel_event.is_set():
            logger.info("task_preempted_during_execution", task_id=task_id)
            raise TaskPreemptedError(f"Task {task_id} was preempted")

        sleep_time = min(check_interval, duration - elapsed)
        await asyncio.sleep(sleep_time)
        elapsed += sleep_time

    # Simulate random failures (5% chance)
    if random.random() < 0.05:
        raise TaskExecutionError(f"Simulated failure for task {task_id}")

    result = {
        "task_id": task_id,
        "name": name,
        "duration_actual": round(elapsed, 2),
        "status": "completed",
    }

    logger.info("task_execution_completed", task_id=task_id, duration_actual=round(elapsed, 2))
    return result
