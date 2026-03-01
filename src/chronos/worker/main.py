import asyncio
import signal
import sys

import httpx
import structlog

from chronos.config.settings import get_settings
from chronos.logging_config.setup import configure_logging
from chronos.redis_client.connection import close_redis, init_redis
from chronos.redis_client.heartbeat_store import HeartbeatStore
from chronos.redis_client.task_assignment import TaskAssignmentQueue
from chronos.worker.executor import TaskExecutor
from chronos.worker.heartbeat import HeartbeatSender
from chronos.worker.resource_reporter import ResourceReporter

logger = structlog.get_logger(__name__)


async def register_with_master(
    master_url: str, hostname: str, cpu_total: float, memory_total: float
) -> str:
    """Register this worker with the master and return the worker ID."""
    async with httpx.AsyncClient(base_url=master_url, timeout=30.0) as client:
        for attempt in range(10):
            try:
                response = await client.post(
                    "/internal/workers/register",
                    json={
                        "hostname": hostname,
                        "cpu_total": cpu_total,
                        "memory_total": memory_total,
                    },
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    return str(data["id"])
                logger.warning(
                    "registration_unexpected_status",
                    status=response.status_code,
                    attempt=attempt + 1,
                )
            except Exception as e:
                logger.warning("registration_failed", error=str(e), attempt=attempt + 1)
            await asyncio.sleep(2 * (attempt + 1))

    raise RuntimeError("Failed to register with master after 10 attempts")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger.info(
        "worker_starting",
        hostname=settings.worker_hostname,
        cpu=settings.worker_cpu_total,
        memory=settings.worker_memory_total,
    )

    # Connect to Redis
    redis = await init_redis(settings.redis_url)

    # Register with master
    worker_id = await register_with_master(
        settings.master_url,
        settings.worker_hostname,
        settings.worker_cpu_total,
        settings.worker_memory_total,
    )
    logger.info("worker_registered", worker_id=worker_id, hostname=settings.worker_hostname)

    # Initialize components
    resource_reporter = ResourceReporter(settings.worker_cpu_total, settings.worker_memory_total)
    heartbeat_store = HeartbeatStore(redis)
    assignment_queue = TaskAssignmentQueue(redis)

    heartbeat_sender = HeartbeatSender(
        worker_id=worker_id,
        heartbeat_store=heartbeat_store,
        resource_reporter=resource_reporter,
        interval=settings.heartbeat_interval_seconds,
        ttl=settings.heartbeat_timeout_seconds,
    )

    executor = TaskExecutor(
        worker_id=worker_id,
        assignment_queue=assignment_queue,
        resource_reporter=resource_reporter,
        master_url=settings.master_url,
    )

    # Set up signal handlers
    shutdown_event = asyncio.Event()

    def handle_signal(sig: int) -> None:
        logger.info("shutdown_signal_received", signal=sig)
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal, sig)

    # Run heartbeat and executor
    tasks = [
        asyncio.create_task(heartbeat_sender.run()),
        asyncio.create_task(executor.run()),
    ]

    # Wait for shutdown
    await shutdown_event.wait()

    # Cleanup
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    await close_redis()
    logger.info("worker_stopped", worker_id=worker_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    sys.exit(0)
