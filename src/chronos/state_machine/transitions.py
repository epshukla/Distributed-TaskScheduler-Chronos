from datetime import datetime, timezone

from chronos.exceptions.task_errors import InvalidStateTransitionError
from chronos.models.enums import TaskState
from chronos.models.task import Task

VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PENDING: {TaskState.SCHEDULED, TaskState.CANCELLED},
    TaskState.SCHEDULED: {TaskState.RUNNING, TaskState.PENDING, TaskState.CANCELLED},
    TaskState.RUNNING: {
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.PREEMPTED,
        TaskState.CANCELLED,
    },
    TaskState.COMPLETED: set(),  # terminal
    TaskState.FAILED: {TaskState.PENDING},  # retry re-enqueue
    TaskState.PREEMPTED: {TaskState.PENDING},  # re-enqueue
    TaskState.CANCELLED: set(),  # terminal
}


def validate_transition(current: TaskState, new: TaskState) -> bool:
    return new in VALID_TRANSITIONS.get(current, set())


def transition_task(task: Task, new_state: TaskState, **kwargs: object) -> Task:
    current = TaskState(task.state)
    if not validate_transition(current, new_state):
        raise InvalidStateTransitionError(current.value, new_state.value)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    task.state = new_state.value
    task.updated_at = now

    if new_state == TaskState.SCHEDULED:
        task.scheduled_at = now
    elif new_state == TaskState.RUNNING:
        task.started_at = now
    elif new_state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
        task.completed_at = now

    if "error" in kwargs:
        task.error = str(kwargs["error"])
    if "result" in kwargs:
        task.result = kwargs["result"]  # type: ignore[assignment]
    if "assigned_worker_id" in kwargs:
        task.assigned_worker_id = kwargs["assigned_worker_id"]  # type: ignore[assignment]

    return task
