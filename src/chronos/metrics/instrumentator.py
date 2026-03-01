from chronos.metrics.collectors import (
    ACTIVE_WORKERS,
    IS_LEADER,
    PREEMPTION_FAILURES,
    PREEMPTIONS,
    SCHEDULER_TICKS,
    TASK_QUEUE_DEPTH,
    TASK_STATE_TRANSITIONS,
    TASKS_COMPLETED,
    TASKS_SUBMITTED,
    WORKER_CPU_UTILIZATION,
    WORKER_FAILURES,
    WORKER_MEMORY_UTILIZATION,
)


def record_task_submitted(priority: int) -> None:
    bucket = "low" if priority <= 30 else "medium" if priority <= 70 else "high"
    TASKS_SUBMITTED.labels(priority_bucket=bucket).inc()


def record_task_completed(state: str) -> None:
    TASKS_COMPLETED.labels(state=state).inc()


def record_state_transition(from_state: str, to_state: str) -> None:
    TASK_STATE_TRANSITIONS.labels(from_state=from_state, to_state=to_state).inc()


def update_queue_depth(depth: int) -> None:
    TASK_QUEUE_DEPTH.set(depth)


def update_active_workers(count: int) -> None:
    ACTIVE_WORKERS.set(count)


def update_worker_utilization(
    worker_id: str, hostname: str, cpu_ratio: float, memory_ratio: float
) -> None:
    WORKER_CPU_UTILIZATION.labels(worker_id=worker_id, hostname=hostname).set(cpu_ratio)
    WORKER_MEMORY_UTILIZATION.labels(worker_id=worker_id, hostname=hostname).set(memory_ratio)


def record_worker_failure() -> None:
    WORKER_FAILURES.inc()


def record_preemption() -> None:
    PREEMPTIONS.inc()


def record_preemption_failure() -> None:
    PREEMPTION_FAILURES.inc()


def record_scheduler_tick(result: str) -> None:
    SCHEDULER_TICKS.labels(result=result).inc()


def update_leader_status(is_leader: bool) -> None:
    IS_LEADER.set(1 if is_leader else 0)
