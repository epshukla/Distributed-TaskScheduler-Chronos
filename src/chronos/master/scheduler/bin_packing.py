from dataclasses import dataclass


@dataclass
class ResourceRequest:
    cpu: float
    memory: float


@dataclass
class WorkerCapacity:
    worker_id: str
    hostname: str
    cpu_available: float
    memory_available: float


def best_fit_schedule(
    task_resources: ResourceRequest,
    workers: list[WorkerCapacity],
) -> WorkerCapacity | None:
    """Best-fit bin-packing: select the worker with the LEAST remaining
    resources after placing the task (tightest fit = least waste).

    Returns None if no worker can accommodate the task.
    """
    candidates: list[tuple[float, WorkerCapacity]] = []
    for w in workers:
        cpu_remaining = w.cpu_available - task_resources.cpu
        mem_remaining = w.memory_available - task_resources.memory
        if cpu_remaining >= 0 and mem_remaining >= 0:
            # Normalize waste: combine CPU and memory waste into single score
            waste = cpu_remaining + (mem_remaining / 1024.0)  # normalize memory to GB
            candidates.append((waste, w))

    if not candidates:
        return None

    # Sort by waste ascending; break ties by worker_id for determinism
    candidates.sort(key=lambda x: (x[0], x[1].worker_id))
    return candidates[0][1]


def first_fit_schedule(
    task_resources: ResourceRequest,
    workers: list[WorkerCapacity],
) -> WorkerCapacity | None:
    """First-fit: return the first worker that can accommodate the task."""
    for w in workers:
        if (
            w.cpu_available >= task_resources.cpu
            and w.memory_available >= task_resources.memory
        ):
            return w
    return None
