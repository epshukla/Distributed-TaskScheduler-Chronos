from enum import StrEnum


class TaskState(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PREEMPTED = "PREEMPTED"
    CANCELLED = "CANCELLED"


class WorkerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DRAINING = "DRAINING"
    DEAD = "DEAD"
    DEREGISTERED = "DEREGISTERED"
