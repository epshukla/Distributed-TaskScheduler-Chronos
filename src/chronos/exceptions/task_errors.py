from chronos.exceptions.base import ChronosError


class TaskNotFoundError(ChronosError):
    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} not found", error_code="TASK_NOT_FOUND")


class InvalidStateTransitionError(ChronosError):
    def __init__(self, current_state: str, new_state: str):
        super().__init__(
            f"Cannot transition from {current_state} to {new_state}",
            error_code="INVALID_STATE_TRANSITION",
        )


class TaskAlreadyCancelledError(ChronosError):
    def __init__(self, task_id: str):
        super().__init__(f"Task {task_id} is already cancelled", error_code="TASK_ALREADY_CANCELLED")
