from dataclasses import dataclass, field

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronos.master.scheduler.bin_packing import ResourceRequest
from chronos.metrics.instrumentator import record_preemption, record_preemption_failure
from chronos.models.enums import TaskState
from chronos.models.task import Task
from chronos.models.worker import Worker
from chronos.redis_client.priority_queue import PriorityQueue
from chronos.redis_client.task_assignment import TaskAssignmentQueue
from chronos.state_machine.transitions import transition_task

logger = structlog.get_logger(__name__)


@dataclass
class WorkerWithTasks:
    worker: Worker
    running_tasks: list[Task] = field(default_factory=list)


@dataclass
class PreemptionPlan:
    worker: Worker
    victims: list[Task]
    waste: float


class PreemptionEngine:
    def __init__(
        self,
        session: AsyncSession,
        priority_queue: PriorityQueue,
        assignment_queue: TaskAssignmentQueue,
    ):
        self._session = session
        self._queue = priority_queue
        self._assignments = assignment_queue

    async def preempt(self, task: Task) -> bool:
        """Attempt to preempt lower-priority tasks to make room for the given task.

        Returns True if preemption succeeded and the task is now scheduled.
        """
        task_resources = ResourceRequest(cpu=task.resource_cpu, memory=task.resource_memory)

        # Get all active workers with their running tasks
        workers_with_tasks = await self._get_workers_with_running_tasks()

        plan = self._find_preemption_candidates(
            task_resources=task_resources,
            task_priority=task.priority,
            workers=workers_with_tasks,
        )

        if plan is None:
            record_preemption_failure()
            logger.warning(
                "preemption_failed_no_candidates",
                task_id=str(task.id),
                priority=task.priority,
            )
            return False

        # Execute the preemption plan
        await self._execute_preemption(plan, task)
        return True

    async def _get_workers_with_running_tasks(self) -> list[WorkerWithTasks]:
        from chronos.models.enums import WorkerStatus

        workers_result = await self._session.execute(
            select(Worker).where(Worker.status == WorkerStatus.ACTIVE)
        )
        workers = list(workers_result.scalars().all())

        result = []
        for worker in workers:
            tasks_result = await self._session.execute(
                select(Task).where(
                    Task.assigned_worker_id == worker.id,
                    Task.state == TaskState.RUNNING,
                )
            )
            running_tasks = list(tasks_result.scalars().all())
            result.append(WorkerWithTasks(worker=worker, running_tasks=running_tasks))

        return result

    @staticmethod
    def _find_preemption_candidates(
        task_resources: ResourceRequest,
        task_priority: int,
        workers: list[WorkerWithTasks],
    ) -> PreemptionPlan | None:
        """Find the optimal preemption plan across all workers.

        For each worker, greedily selects lowest-priority running tasks
        until enough resources are freed. Returns the plan with minimum waste.
        """
        best_plan: PreemptionPlan | None = None

        for wt in workers:
            # Only consider tasks with strictly lower priority
            evictable = sorted(
                [t for t in wt.running_tasks if t.priority < task_priority],
                key=lambda t: t.priority,
            )
            if not evictable:
                continue

            freed_cpu = wt.worker.cpu_available
            freed_mem = wt.worker.memory_available
            victims: list[Task] = []

            for victim in evictable:
                if freed_cpu >= task_resources.cpu and freed_mem >= task_resources.memory:
                    break
                freed_cpu += victim.resource_cpu
                freed_mem += victim.resource_memory
                victims.append(victim)

            if freed_cpu >= task_resources.cpu and freed_mem >= task_resources.memory:
                waste = (freed_cpu - task_resources.cpu) + (
                    (freed_mem - task_resources.memory) / 1024.0
                )
                if best_plan is None or waste < best_plan.waste:
                    best_plan = PreemptionPlan(
                        worker=wt.worker, victims=victims, waste=waste
                    )

        return best_plan

    async def _execute_preemption(self, plan: PreemptionPlan, new_task: Task) -> None:
        """Execute the preemption: evict victims, schedule the new task."""
        for victim in plan.victims:
            old_state = victim.state
            transition_task(victim, TaskState.PREEMPTED)

            # Signal worker to stop victim
            await self._assignments.send_preempt_signal(
                str(plan.worker.id), str(victim.id)
            )

            # Free resources on the worker
            plan.worker.cpu_available += victim.resource_cpu
            plan.worker.memory_available += victim.resource_memory

            # Re-enqueue victim if retries remain
            if victim.retry_count < victim.max_retries:
                victim.retry_count += 1
                transition_task(victim, TaskState.PENDING)
                victim.assigned_worker_id = None
                await self._queue.enqueue(str(victim.id), victim.priority)

            record_preemption()
            logger.info(
                "task_preempted",
                victim_id=str(victim.id),
                victim_priority=victim.priority,
                new_task_id=str(new_task.id),
                new_task_priority=new_task.priority,
                worker=plan.worker.hostname,
            )

        # Schedule the new task on the freed worker
        transition_task(new_task, TaskState.SCHEDULED, assigned_worker_id=plan.worker.id)
        new_task.assigned_worker_id = plan.worker.id
        plan.worker.cpu_available -= new_task.resource_cpu
        plan.worker.memory_available -= new_task.resource_memory

        await self._assignments.assign_task(str(plan.worker.id), str(new_task.id))

        logger.info(
            "task_scheduled_via_preemption",
            task_id=str(new_task.id),
            worker=plan.worker.hostname,
            victims_count=len(plan.victims),
        )
