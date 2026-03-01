from chronos.exceptions.base import ChronosError


class InsufficientResourcesError(ChronosError):
    def __init__(self, cpu_needed: float, memory_needed: float):
        super().__init__(
            f"Insufficient resources: need {cpu_needed} CPU, {memory_needed} MB memory",
            error_code="INSUFFICIENT_RESOURCES",
        )


class PreemptionFailedError(ChronosError):
    def __init__(self, task_id: str, reason: str = "no suitable victims"):
        super().__init__(
            f"Preemption failed for task {task_id}: {reason}",
            error_code="PREEMPTION_FAILED",
        )
