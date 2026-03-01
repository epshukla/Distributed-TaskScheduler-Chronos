import asyncio

import docker
import docker.errors
import psutil
import structlog

logger = structlog.get_logger(__name__)


class ResourceReporter:
    """Tracks resource usage on a worker node using both scheduler-level
    accounting (reserve/release) and real OS-level metrics (psutil + Docker)."""

    def __init__(
        self,
        cpu_total: float,
        memory_total: float,
        worker_id: str = "",
        auto_detect: bool = True,
    ):
        self._lock = asyncio.Lock()

        # Scheduler-tracked reservations
        self._cpu_reserved: float = 0.0
        self._memory_reserved: float = 0.0

        # Use psutil auto-detection or fall back to configured values
        if auto_detect:
            self.cpu_total = float(psutil.cpu_count(logical=True) or cpu_total)
            self.memory_total = round(psutil.virtual_memory().total / (1024 * 1024), 1)
        else:
            self.cpu_total = cpu_total
            self.memory_total = memory_total

        self._worker_id = worker_id

    @property
    def cpu_available(self) -> float:
        """Scheduler-tracked CPU available (total - reserved)."""
        return max(0.0, self.cpu_total - self._cpu_reserved)

    @property
    def memory_available(self) -> float:
        """Scheduler-tracked memory available (total - reserved)."""
        return max(0.0, self.memory_total - self._memory_reserved)

    async def reserve(self, cpu: float, memory: float) -> None:
        async with self._lock:
            self._cpu_reserved += cpu
            self._memory_reserved += memory

    async def release(self, cpu: float, memory: float) -> None:
        async with self._lock:
            self._cpu_reserved = max(0.0, self._cpu_reserved - cpu)
            self._memory_reserved = max(0.0, self._memory_reserved - memory)

    def get_real_usage(self) -> dict:
        """Get actual OS-level resource metrics from psutil."""
        cpu_count = psutil.cpu_count(logical=True) or 1
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        actual_cpu_used = (cpu_percent / 100.0) * cpu_count
        actual_mem_used_mb = round((mem.total - mem.available) / (1024 * 1024), 1)
        actual_mem_total_mb = round(mem.total / (1024 * 1024), 1)

        return {
            "actual_cpu_used": round(actual_cpu_used, 2),
            "actual_cpu_total": cpu_count,
            "actual_memory_used": actual_mem_used_mb,
            "actual_memory_total": actual_mem_total_mb,
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(mem.percent, 1),
        }

    def get_container_usage(self) -> dict:
        """Query Docker for container-level resource usage from running Chronos tasks."""
        result = {
            "container_count": 0,
            "container_cpu_usage": 0.0,
            "container_memory_usage": 0.0,
        }
        if not self._worker_id:
            return result

        try:
            client = docker.from_env()
            containers = client.containers.list(
                filters={"label": f"chronos.worker_id={self._worker_id}"}
            )
            result["container_count"] = len(containers)

            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    # CPU usage calculation
                    cpu_delta = (
                        stats["cpu_stats"]["cpu_usage"]["total_usage"]
                        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    )
                    system_delta = (
                        stats["cpu_stats"]["system_cpu_usage"]
                        - stats["precpu_stats"]["system_cpu_usage"]
                    )
                    num_cpus = stats["cpu_stats"].get(
                        "online_cpus",
                        len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1])),
                    )
                    if system_delta > 0 and cpu_delta > 0:
                        cpu_usage = (cpu_delta / system_delta) * num_cpus
                        result["container_cpu_usage"] += round(cpu_usage, 3)

                    # Memory usage
                    mem_usage = stats["memory_stats"].get("usage", 0)
                    mem_cache = stats["memory_stats"].get("stats", {}).get("cache", 0)
                    result["container_memory_usage"] += round(
                        (mem_usage - mem_cache) / (1024 * 1024), 1
                    )
                except Exception:
                    pass

        except Exception as e:
            logger.debug("container_stats_error", error=str(e))

        return result

    def to_dict(self) -> dict:
        """Full resource report combining scheduler-tracked and real metrics."""
        real = self.get_real_usage()
        containers = self.get_container_usage()

        return {
            # Scheduler-tracked (what the scheduler thinks)
            "cpu_total": self.cpu_total,
            "cpu_available": self.cpu_available,
            "memory_total": self.memory_total,
            "memory_available": self.memory_available,
            "cpu_reserved": self._cpu_reserved,
            "memory_reserved": self._memory_reserved,
            # Actual OS-level metrics (what's really happening)
            **real,
            # Container-level metrics
            **containers,
        }
