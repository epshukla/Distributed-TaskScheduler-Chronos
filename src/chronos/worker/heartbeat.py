import asyncio
import time

import structlog

from chronos.redis_client.heartbeat_store import HeartbeatStore
from chronos.worker.resource_reporter import ResourceReporter

logger = structlog.get_logger(__name__)


class HeartbeatSender:
    """Sends periodic heartbeats to Redis with resource availability.

    Includes both scheduler-tracked (reserved) and actual (psutil-measured)
    resource data so the dashboard can show real vs allocated usage.
    """

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
                full_report = self._reporter.to_dict()
                payload = {
                    # Scheduler-tracked values (used by master for scheduling decisions)
                    "cpu_available": full_report["cpu_available"],
                    "memory_available": full_report["memory_available"],
                    "timestamp": time.time(),
                    # Real metrics for dashboard display
                    "actual_cpu_used": full_report.get("actual_cpu_used", 0),
                    "actual_cpu_total": full_report.get("actual_cpu_total", 0),
                    "actual_memory_used": full_report.get("actual_memory_used", 0),
                    "actual_memory_total": full_report.get("actual_memory_total", 0),
                    "cpu_percent": full_report.get("cpu_percent", 0),
                    "memory_percent": full_report.get("memory_percent", 0),
                    "container_count": full_report.get("container_count", 0),
                    "container_cpu_usage": full_report.get("container_cpu_usage", 0),
                    "container_memory_usage": full_report.get("container_memory_usage", 0),
                }
                await self._store.send_heartbeat(self._worker_id, payload, self._ttl)
            except asyncio.CancelledError:
                logger.info("heartbeat_sender_stopped", worker_id=self._worker_id)
                return
            except Exception as e:
                logger.error("heartbeat_send_failed", worker_id=self._worker_id, error=str(e))
            await asyncio.sleep(self._interval)
