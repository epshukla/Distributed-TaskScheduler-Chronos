import asyncio
import time

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chronos.config.settings import Settings
from chronos.etcd_client.leader_election import LeaderElection
from chronos.master.scheduler.bin_packing import ResourceRequest, WorkerCapacity, best_fit_schedule
from chronos.master.scheduler.preemption import PreemptionEngine
from chronos.master.events import event_bus
from chronos.metrics.collectors import SCHEDULER_TICK_DURATION, SCHEDULING_LATENCY
from chronos.metrics.instrumentator import record_scheduler_tick, update_queue_depth
from chronos.models.enums import TaskState, WorkerStatus
from chronos.models.task import Task
from chronos.models.worker import Worker
from chronos.redis_client.distributed_lock import DistributedLock
from chronos.redis_client.priority_queue import PriorityQueue
from chronos.redis_client.task_assignment import TaskAssignmentQueue
from chronos.state_machine.transitions import transition_task

logger = structlog.get_logger(__name__)


class SchedulerLoop:
    """Main scheduling loop: dequeues tasks and assigns them to workers."""

    def __init__(
        self,
        db_factory: async_sessionmaker[AsyncSession],
        redis: object,
        leader_election: LeaderElection | None,
        settings: Settings,
    ):
        self._db_factory = db_factory
        self._redis = redis
        self._priority_queue = PriorityQueue(redis)  # type: ignore[arg-type]
        self._assignment_queue = TaskAssignmentQueue(redis)  # type: ignore[arg-type]
        self._lock = DistributedLock(redis)  # type: ignore[arg-type]
        self._leader_election = leader_election
        self._interval = settings.scheduler_interval_seconds
        self._batch_size = settings.scheduler_batch_size

    async def run(self) -> None:
        logger.info("scheduler_loop_started")
        # Reconcile on startup
        await self._reconcile_pending_tasks()
        await self._reconcile_scheduled_tasks()
        tick_count = 0
        while True:
            try:
                if self._is_leader():
                    await self._tick()
                    tick_count += 1
                    # Periodic reconciliation every 60 ticks (~60s)
                    if tick_count % 60 == 0:
                        await self._reconcile_pending_tasks()
                        await self._reconcile_scheduled_tasks()
            except asyncio.CancelledError:
                logger.info("scheduler_loop_stopped")
                return
            except Exception as e:
                logger.error("scheduler_tick_error", error=str(e))
            await asyncio.sleep(self._interval)

    async def _reconcile_pending_tasks(self) -> None:
        """Re-enqueue PENDING tasks that are missing from the Redis queue."""
        try:
            async with self._db_factory() as session:
                result = await session.execute(
                    select(Task).where(Task.state == TaskState.PENDING)
                )
                pending_tasks = list(result.scalars().all())
                enqueued = 0
                for task in pending_tasks:
                    if not await self._priority_queue.contains(str(task.id)):
                        await self._priority_queue.enqueue(str(task.id), task.priority)
                        enqueued += 1
                if enqueued:
                    logger.info("reconciled_pending_tasks", enqueued=enqueued, total_pending=len(pending_tasks))
        except Exception as e:
            logger.error("reconciliation_error", error=str(e))

    async def _reconcile_scheduled_tasks(self) -> None:
        """Re-push SCHEDULED tasks whose Redis assignment was lost (e.g. after restart)."""
        try:
            async with self._db_factory() as session:
                result = await session.execute(
                    select(Task).where(
                        Task.state == TaskState.SCHEDULED,
                        Task.assigned_worker_id.isnot(None),
                    )
                )
                scheduled_tasks = list(result.scalars().all())
                reassigned = 0
                for task in scheduled_tasks:
                    worker_id = str(task.assigned_worker_id)
                    # Check if the worker still exists and is ACTIVE
                    worker = await session.get(Worker, task.assigned_worker_id)
                    if worker and worker.status == WorkerStatus.ACTIVE:
                        # Re-push assignment to Redis
                        await self._assignment_queue.assign_task(worker_id, str(task.id))
                        reassigned += 1
                    else:
                        # Worker is dead — reset task to PENDING for rescheduling
                        transition_task(task, TaskState.PENDING)
                        task.assigned_worker_id = None
                        await self._priority_queue.enqueue(str(task.id), task.priority)
                        reassigned += 1
                if reassigned:
                    logger.info(
                        "reconciled_scheduled_tasks",
                        reassigned=reassigned,
                        total_scheduled=len(scheduled_tasks),
                    )
        except Exception as e:
            logger.error("scheduled_reconciliation_error", error=str(e))

    def _is_leader(self) -> bool:
        if self._leader_election is None:
            return True
        return self._leader_election.is_leader

    async def _tick(self) -> None:
        start = time.perf_counter()

        # Update queue depth metric
        queue_size = await self._priority_queue.size()
        update_queue_depth(queue_size)

        if queue_size == 0:
            return

        try:
            async with self._lock.lock("chronos:lock:scheduler", timeout=10, blocking_timeout=2):
                await self._schedule_batch()
                record_scheduler_tick("success")
        except TimeoutError:
            record_scheduler_tick("lock_timeout")
            logger.debug("scheduler_lock_contention")
        except Exception as e:
            record_scheduler_tick("error")
            logger.error("scheduler_tick_failed", error=str(e))

        duration = time.perf_counter() - start
        SCHEDULER_TICK_DURATION.observe(duration)

    async def _schedule_batch(self) -> None:
        # Dequeue a batch of task IDs
        task_ids = await self._priority_queue.dequeue_batch(self._batch_size)
        if not task_ids:
            return

        async with self._db_factory() as session:
            async with session.begin():
                # Get available workers
                workers = await self._get_available_workers(session)
                if not workers:
                    # Re-enqueue all tasks — no workers available
                    for task_id in task_ids:
                        task = await session.get(Task, task_id)
                        if task and task.state == TaskState.PENDING:
                            await self._priority_queue.enqueue(task_id, task.priority)
                    logger.warning("no_available_workers", requeued=len(task_ids))
                    return

                for task_id in task_ids:
                    task = await session.get(Task, task_id)
                    if task is None or task.state != TaskState.PENDING:
                        continue

                    scheduled = await self._try_schedule_task(session, task, workers)
                    if not scheduled:
                        # Try preemption
                        preemption_engine = PreemptionEngine(
                            session, self._priority_queue, self._assignment_queue
                        )
                        preempted = await preemption_engine.preempt(task)
                        if not preempted:
                            # Re-enqueue: no capacity at all
                            await self._priority_queue.enqueue(str(task.id), task.priority)

    async def _get_available_workers(self, session: AsyncSession) -> list[WorkerCapacity]:
        result = await session.execute(
            select(Worker).where(Worker.status == WorkerStatus.ACTIVE)
        )
        workers = list(result.scalars().all())
        return [
            WorkerCapacity(
                worker_id=str(w.id),
                hostname=w.hostname,
                cpu_available=w.cpu_available,
                memory_available=w.memory_available,
            )
            for w in workers
        ]

    async def _try_schedule_task(
        self,
        session: AsyncSession,
        task: Task,
        workers: list[WorkerCapacity],
    ) -> bool:
        """Try to schedule a task using best-fit bin-packing. Returns True on success."""
        resources = ResourceRequest(cpu=task.resource_cpu, memory=task.resource_memory)
        selected = best_fit_schedule(resources, workers)

        if selected is None:
            return False

        # Transition task state
        import uuid as _uuid

        worker_uuid = _uuid.UUID(selected.worker_id)
        transition_task(task, TaskState.SCHEDULED, assigned_worker_id=worker_uuid)
        task.assigned_worker_id = worker_uuid

        # Update worker available resources in the local list
        selected.cpu_available -= task.resource_cpu
        selected.memory_available -= task.resource_memory

        # Also update the worker in DB
        worker = await session.get(Worker, worker_uuid)
        if worker:
            worker.cpu_available -= task.resource_cpu
            worker.memory_available -= task.resource_memory

        # Push to worker assignment queue
        await self._assignment_queue.assign_task(selected.worker_id, str(task.id))

        # Track scheduling latency
        if task.created_at:
            latency = (task.scheduled_at - task.created_at).total_seconds() if task.scheduled_at else 0
            SCHEDULING_LATENCY.observe(latency)

        logger.info(
            "task_scheduled",
            task_id=str(task.id),
            worker=selected.hostname,
            priority=task.priority,
        )

        await event_bus.publish("task_scheduled", {
            "task_id": str(task.id),
            "name": task.name,
            "worker_id": selected.worker_id,
            "worker_hostname": selected.hostname,
            "priority": task.priority,
            "resource_cpu": task.resource_cpu,
            "resource_memory": task.resource_memory,
        })

        return True
