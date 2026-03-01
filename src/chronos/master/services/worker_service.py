import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronos.exceptions import WorkerNotFoundError
from chronos.master.events import event_bus
from chronos.models.enums import WorkerStatus
from chronos.models.worker import Worker
from chronos.schemas.worker import WorkerRegister, WorkerResponse

logger = structlog.get_logger(__name__)


class WorkerService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def register_worker(self, data: WorkerRegister) -> WorkerResponse:
        # Check if worker with hostname already exists
        result = await self._session.execute(
            select(Worker).where(Worker.hostname == data.hostname)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Re-register: update status and resources
            existing.status = WorkerStatus.ACTIVE
            existing.cpu_total = data.cpu_total
            existing.cpu_available = data.cpu_total
            existing.memory_total = data.memory_total
            existing.memory_available = data.memory_total
            existing.last_heartbeat = datetime.now(timezone.utc).replace(tzinfo=None)
            await self._session.flush()
            logger.info("worker_re_registered", worker_id=str(existing.id), hostname=data.hostname)
            await event_bus.publish("worker_registered", {
                "worker_id": str(existing.id),
                "hostname": data.hostname,
                "cpu_total": data.cpu_total,
                "memory_total": data.memory_total,
                "status": WorkerStatus.ACTIVE.value,
            })
            return WorkerResponse.model_validate(existing)

        worker = Worker(
            id=uuid.uuid4(),
            hostname=data.hostname,
            status=WorkerStatus.ACTIVE,
            cpu_total=data.cpu_total,
            cpu_available=data.cpu_total,
            memory_total=data.memory_total,
            memory_available=data.memory_total,
        )
        self._session.add(worker)
        await self._session.flush()
        logger.info("worker_registered", worker_id=str(worker.id), hostname=data.hostname)
        await event_bus.publish("worker_registered", {
            "worker_id": str(worker.id),
            "hostname": data.hostname,
            "cpu_total": data.cpu_total,
            "memory_total": data.memory_total,
            "status": WorkerStatus.ACTIVE.value,
        })
        return WorkerResponse.model_validate(worker)

    async def get_worker(self, worker_id: uuid.UUID) -> WorkerResponse:
        worker = await self._session.get(Worker, worker_id)
        if worker is None:
            raise WorkerNotFoundError(str(worker_id))
        return WorkerResponse.model_validate(worker)

    async def list_workers(self, status: str | None = None) -> list[WorkerResponse]:
        query = select(Worker)
        if status:
            query = query.where(Worker.status == status)
        query = query.order_by(Worker.registered_at.desc())
        result = await self._session.execute(query)
        workers = list(result.scalars().all())
        return [WorkerResponse.model_validate(w) for w in workers]

    async def get_available_workers(self) -> list[Worker]:
        result = await self._session.execute(
            select(Worker).where(Worker.status == WorkerStatus.ACTIVE)
        )
        return list(result.scalars().all())

    async def update_worker_resources(
        self,
        worker_id: uuid.UUID,
        cpu_available: float,
        memory_available: float,
    ) -> None:
        worker = await self._session.get(Worker, worker_id)
        if worker is None:
            raise WorkerNotFoundError(str(worker_id))
        worker.cpu_available = cpu_available
        worker.memory_available = memory_available
        worker.last_heartbeat = datetime.now(timezone.utc).replace(tzinfo=None)

    async def mark_worker_dead(self, worker_id: uuid.UUID) -> None:
        worker = await self._session.get(Worker, worker_id)
        if worker:
            worker.status = WorkerStatus.DEAD
            logger.warning("worker_marked_dead", worker_id=str(worker_id))
            await event_bus.publish("worker_dead", {
                "worker_id": str(worker_id),
                "hostname": worker.hostname,
            })

    async def heartbeat(self, worker_id: uuid.UUID, cpu_available: float, memory_available: float) -> None:
        worker = await self._session.get(Worker, worker_id)
        if worker is None:
            raise WorkerNotFoundError(str(worker_id))
        worker.last_heartbeat = datetime.now(timezone.utc).replace(tzinfo=None)
        worker.cpu_available = cpu_available
        worker.memory_available = memory_available
        await event_bus.publish("worker_heartbeat", {
            "worker_id": str(worker_id),
            "hostname": worker.hostname,
            "cpu_available": cpu_available,
            "memory_available": memory_available,
            "cpu_total": worker.cpu_total,
            "memory_total": worker.memory_total,
        })
