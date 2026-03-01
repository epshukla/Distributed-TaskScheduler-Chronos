import uuid

import pytest

from chronos.master.scheduler.bin_packing import ResourceRequest
from chronos.master.scheduler.preemption import PreemptionEngine, WorkerWithTasks
from chronos.models.enums import TaskState, WorkerStatus
from chronos.models.task import Task
from chronos.models.worker import Worker


def make_worker(cpu_avail: float = 0.0, mem_avail: float = 0.0) -> Worker:
    w = Worker(
        id=uuid.uuid4(),
        hostname="test-worker",
        status=WorkerStatus.ACTIVE,
        cpu_total=8.0,
        cpu_available=cpu_avail,
        memory_total=8192.0,
        memory_available=mem_avail,
    )
    return w


def make_task(priority: int, cpu: float = 1.0, memory: float = 256.0) -> Task:
    return Task(
        id=uuid.uuid4(),
        name=f"task-p{priority}",
        priority=priority,
        state=TaskState.RUNNING,
        resource_cpu=cpu,
        resource_memory=memory,
    )


class TestFindPreemptionCandidates:
    def test_no_evictable_tasks(self):
        """No tasks have lower priority than the incoming task."""
        worker = make_worker(cpu_avail=0.0, mem_avail=0.0)
        running = [make_task(priority=90, cpu=2.0, memory=512.0)]
        wt = WorkerWithTasks(worker=worker, running_tasks=running)

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.0, 512.0), task_priority=50, workers=[wt]
        )
        assert plan is None

    def test_single_victim_sufficient(self):
        worker = make_worker(cpu_avail=0.0, mem_avail=0.0)
        running = [make_task(priority=10, cpu=2.0, memory=512.0)]
        wt = WorkerWithTasks(worker=worker, running_tasks=running)

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.0, 512.0), task_priority=50, workers=[wt]
        )
        assert plan is not None
        assert len(plan.victims) == 1
        assert plan.victims[0].priority == 10

    def test_multiple_victims_needed(self):
        worker = make_worker(cpu_avail=0.0, mem_avail=0.0)
        running = [
            make_task(priority=10, cpu=1.0, memory=256.0),
            make_task(priority=20, cpu=1.0, memory=256.0),
            make_task(priority=30, cpu=1.0, memory=256.0),
        ]
        wt = WorkerWithTasks(worker=worker, running_tasks=running)

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.5, 600.0), task_priority=50, workers=[wt]
        )
        assert plan is not None
        assert len(plan.victims) == 3

    def test_selects_lowest_priority_victims(self):
        worker = make_worker(cpu_avail=0.0, mem_avail=0.0)
        running = [
            make_task(priority=10, cpu=2.0, memory=512.0),
            make_task(priority=40, cpu=2.0, memory=512.0),
        ]
        wt = WorkerWithTasks(worker=worker, running_tasks=running)

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.0, 512.0), task_priority=50, workers=[wt]
        )
        assert plan is not None
        assert len(plan.victims) == 1
        assert plan.victims[0].priority == 10

    def test_selects_worker_with_minimum_waste(self):
        w1 = make_worker(cpu_avail=0.0, mem_avail=0.0)
        w1.hostname = "w1"
        w2 = make_worker(cpu_avail=0.0, mem_avail=0.0)
        w2.hostname = "w2"

        wt1 = WorkerWithTasks(
            worker=w1,
            running_tasks=[make_task(priority=10, cpu=4.0, memory=2048.0)],  # big waste
        )
        wt2 = WorkerWithTasks(
            worker=w2,
            running_tasks=[make_task(priority=10, cpu=2.0, memory=512.0)],  # small waste
        )

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.0, 512.0), task_priority=50, workers=[wt1, wt2]
        )
        assert plan is not None
        assert plan.worker.hostname == "w2"

    def test_equal_priority_not_evicted(self):
        worker = make_worker(cpu_avail=0.0, mem_avail=0.0)
        running = [make_task(priority=50, cpu=2.0, memory=512.0)]
        wt = WorkerWithTasks(worker=worker, running_tasks=running)

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.0, 512.0), task_priority=50, workers=[wt]
        )
        assert plan is None

    def test_partial_resources_from_worker_available(self):
        worker = make_worker(cpu_avail=1.0, mem_avail=256.0)
        running = [make_task(priority=10, cpu=1.0, memory=256.0)]
        wt = WorkerWithTasks(worker=worker, running_tasks=running)

        plan = PreemptionEngine._find_preemption_candidates(
            ResourceRequest(2.0, 512.0), task_priority=50, workers=[wt]
        )
        assert plan is not None
        assert len(plan.victims) == 1
