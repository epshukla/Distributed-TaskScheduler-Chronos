import asyncio
import time

import structlog

from chronos.redis_client.heartbeat_store import HeartbeatStore
from chronos.worker.resource_reporter import ResourceReporter

logger = structlog.get_logger(__name__)


class HeartbeatSender:
    """Sends periodic heartbeats to Redis with resource availability."""

    def __init__(
        self,
        worker_id: str,
        heartbeat_store: HeartbeatStore,
        resource_reporter: ResourceReporter,
        interval: int = 5,
        ttl: int = 15,
    ):
        self._worker_id = worker_id
        self._store = heartbeat_store
        self._reporter = resource_reporter
        self._interval = interval
        self._ttl = ttl

    async def run(self) -> None:
        logger.info("heartbeat_sender_started", worker_id=self._worker_id)
        while True:
            try:
                payload = {
                    "cpu_available": self._reporter.cpu_available,
                    "memory_available": self._reporter.memory_available,
                    "timestamp": time.time(),
                }
                await self._store.send_heartbeat(self._worker_id, payload, self._ttl)
            except asyncio.CancelledError:
                logger.info("heartbeat_sender_stopped", worker_id=self._worker_id)
                return
            except Exception as e:
                logger.error("heartbeat_send_failed", worker_id=self._worker_id, error=str(e))
            await asyncio.sleep(self._interval)
