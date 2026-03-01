import asyncio

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from chronos.config.settings import Settings
from chronos.etcd_client.leader_election import LeaderElection
from chronos.master.events import event_bus
from chronos.metrics.instrumentator import record_worker_failure, update_active_workers
from chronos.models.enums import TaskState, WorkerStatus
from chronos.models.task import Task
from chronos.models.worker import Worker
from chronos.redis_client.heartbeat_store import HeartbeatStore
from chronos.redis_client.priority_queue import PriorityQueue
from chronos.state_machine.transitions import transition_task

logger = structlog.get_logger(__name__)


class FailureDetector:
    """Detects dead workers via heartbeat timeout and reassigns their tasks."""

    def __init__(
        self,
        db_factory: async_sessionmaker[AsyncSession],
        redis: object,
        leader_election: LeaderElection | None,
        settings: Settings,
    ):
        self._db_factory = db_factory
        self._heartbeat_store = HeartbeatStore(redis)  # type: ignore[arg-type]
        self._priority_queue = PriorityQueue(redis)  # type: ignore[arg-type]
        self._leader_election = leader_election
        self._interval = settings.failure_check_interval_seconds

    async def run(self) -> None:
        logger.info("failure_detector_started")
        while True:
            try:
                if self._is_leader():
                    await self._check_all_workers()
            except asyncio.CancelledError:
                logger.info("failure_detector_stopped")
                return
            except Exception as e:
                logger.error("failure_detection_error", error=str(e))
            await asyncio.sleep(self._interval)

    def _is_leader(self) -> bool:
        if self._leader_election is None:
            return True  # standalone mode
        return self._leader_election.is_leader

    async def _check_all_workers(self) -> None:
        async with self._db_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(Worker).where(Worker.status == WorkerStatus.ACTIVE)
                )
                active_workers = list(result.scalars().all())
                update_active_workers(len(active_workers))

                for worker in active_workers:
                    alive = await self._heartbeat_store.is_alive(str(worker.id))
                    if not alive:
                        await self._handle_dead_worker(session, worker)

    async def _handle_dead_worker(self, session: AsyncSession, worker: Worker) -> None:
        logger.warning(
            "worker_dead",
            worker_id=str(worker.id),
            hostname=worker.hostname,
        )
        worker.status = WorkerStatus.DEAD
        record_worker_failure()

        await event_bus.publish("worker_dead", {
            "worker_id": str(worker.id),
            "hostname": worker.hostname,
        })

        # Find all tasks assigned to this worker
        result = await session.execute(
            select(Task).where(
                Task.assigned_worker_id == worker.id,
                Task.state.in_([TaskState.RUNNING, TaskState.SCHEDULED]),
            )
        )
        orphaned_tasks = list(result.scalars().all())

        for task in orphaned_tasks:
            if task.retry_count < task.max_retries:
                old_state = task.state
                transition_task(task, TaskState.PENDING)
                task.retry_count += 1
                task.assigned_worker_id = None
                await self._priority_queue.enqueue(str(task.id), task.priority)
                logger.info(
                    "orphaned_task_requeued",
                    task_id=str(task.id),
                    from_state=old_state,
                    retry_count=task.retry_count,
                )
                await event_bus.publish("task_state_changed", {
                    "task_id": str(task.id),
                    "name": task.name,
                    "from_state": old_state,
                    "to_state": TaskState.PENDING.value,
                    "reason": f"worker_{worker.hostname}_died",
                })
            else:
                transition_task(
                    task,
                    TaskState.FAILED,
                    error=f"Worker {worker.hostname} died, retries exhausted",
                )
                logger.info(
                    "orphaned_task_failed",
                    task_id=str(task.id),
                    reason="retries_exhausted",
                )
                await event_bus.publish("task_state_changed", {
                    "task_id": str(task.id),
                    "name": task.name,
                    "from_state": old_state if task.retry_count > 0 else task.state,
                    "to_state": TaskState.FAILED.value,
                    "reason": "retries_exhausted",
                })

        logger.info(
            "dead_worker_tasks_handled",
            worker_id=str(worker.id),
            orphaned_count=len(orphaned_tasks),
        )
