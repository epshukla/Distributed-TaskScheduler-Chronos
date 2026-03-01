from prometheus_client import Counter, Gauge, Histogram, Info

# Task metrics
TASKS_SUBMITTED = Counter(
    "chronos_tasks_submitted_total",
    "Total tasks submitted",
    ["priority_bucket"],
)
TASKS_COMPLETED = Counter(
    "chronos_tasks_completed_total",
    "Total tasks completed by final state",
    ["state"],
)
TASK_QUEUE_DEPTH = Gauge(
    "chronos_task_queue_depth",
    "Current number of tasks in the scheduling queue",
)
SCHEDULING_LATENCY = Histogram(
    "chronos_scheduling_latency_seconds",
    "Time from PENDING to SCHEDULED",
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 5, 10, 30],
)
TASK_EXECUTION_DURATION = Histogram(
    "chronos_task_execution_duration_seconds",
    "Task execution time",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)
TASK_STATE_TRANSITIONS = Counter(
    "chronos_task_state_transitions_total",
    "Total state transitions",
    ["from_state", "to_state"],
)

# Worker metrics
ACTIVE_WORKERS = Gauge(
    "chronos_active_workers",
    "Number of active workers",
)
WORKER_CPU_UTILIZATION = Gauge(
    "chronos_worker_cpu_utilization_ratio",
    "Worker CPU utilization (0-1)",
    ["worker_id", "hostname"],
)
WORKER_MEMORY_UTILIZATION = Gauge(
    "chronos_worker_memory_utilization_ratio",
    "Worker memory utilization (0-1)",
    ["worker_id", "hostname"],
)
WORKER_FAILURES = Counter(
    "chronos_worker_failures_total",
    "Total worker failures detected",
)

# Preemption metrics
PREEMPTIONS = Counter(
    "chronos_preemptions_total",
    "Total tasks preempted",
)
PREEMPTION_FAILURES = Counter(
    "chronos_preemption_failures_total",
    "Failed preemption attempts",
)

# Scheduler metrics
SCHEDULER_TICKS = Counter(
    "chronos_scheduler_ticks_total",
    "Total scheduler ticks",
    ["result"],
)
SCHEDULER_TICK_DURATION = Histogram(
    "chronos_scheduler_tick_duration_seconds",
    "Scheduler tick duration",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1],
)

# Leader election
IS_LEADER = Gauge(
    "chronos_is_leader",
    "Whether this instance is the leader (1=leader, 0=follower)",
)

# Build info
BUILD_INFO = Info(
    "chronos_build",
    "Build information",
)
