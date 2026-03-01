# Redis key patterns
REDIS_TASK_QUEUE_KEY = "chronos:task_queue"
REDIS_WORKER_HEARTBEAT_PREFIX = "chronos:worker:"
REDIS_WORKER_HEARTBEAT_SUFFIX = ":heartbeat"
REDIS_WORKER_ASSIGNMENTS_PREFIX = "chronos:worker:"
REDIS_WORKER_ASSIGNMENTS_SUFFIX = ":assignments"
REDIS_WORKER_PREEMPT_PREFIX = "chronos:worker:"
REDIS_WORKER_PREEMPT_SUFFIX = ":preempt"
REDIS_WORKER_ACTIVE_TASKS_PREFIX = "chronos:worker:"
REDIS_WORKER_ACTIVE_TASKS_SUFFIX = ":active_tasks"
REDIS_LOCK_SCHEDULER = "chronos:lock:scheduler"
REDIS_LOCK_PREEMPTION = "chronos:lock:preemption"

# etcd keys
ETCD_ELECTION_KEY = "/chronos/leader"
ETCD_LEASE_TTL = 15
ETCD_KEEPALIVE_INTERVAL = 5

# Default resource values
DEFAULT_TASK_CPU = 1.0
DEFAULT_TASK_MEMORY = 256.0
DEFAULT_WORKER_CPU = 4.0
DEFAULT_WORKER_MEMORY = 4096.0

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def worker_heartbeat_key(worker_id: str) -> str:
    return f"{REDIS_WORKER_HEARTBEAT_PREFIX}{worker_id}{REDIS_WORKER_HEARTBEAT_SUFFIX}"


def worker_assignments_key(worker_id: str) -> str:
    return f"{REDIS_WORKER_ASSIGNMENTS_PREFIX}{worker_id}{REDIS_WORKER_ASSIGNMENTS_SUFFIX}"


def worker_preempt_key(worker_id: str) -> str:
    return f"{REDIS_WORKER_PREEMPT_PREFIX}{worker_id}{REDIS_WORKER_PREEMPT_SUFFIX}"


def worker_active_tasks_key(worker_id: str) -> str:
    return f"{REDIS_WORKER_ACTIVE_TASKS_PREFIX}{worker_id}{REDIS_WORKER_ACTIVE_TASKS_SUFFIX}"
