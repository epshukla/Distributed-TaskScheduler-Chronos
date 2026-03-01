from chronos.exceptions.base import ChronosError


class WorkerNotFoundError(ChronosError):
    def __init__(self, worker_id: str):
        super().__init__(f"Worker {worker_id} not found", error_code="WORKER_NOT_FOUND")


class WorkerUnavailableError(ChronosError):
    def __init__(self, worker_id: str):
        super().__init__(
            f"Worker {worker_id} is unavailable", error_code="WORKER_UNAVAILABLE"
        )
