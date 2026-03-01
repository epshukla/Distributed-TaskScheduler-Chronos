import asyncio


class ResourceReporter:
    """Tracks resource usage on a worker node."""

    def __init__(self, cpu_total: float, memory_total: float):
        self.cpu_total = cpu_total
        self.memory_total = memory_total
        self._cpu_reserved: float = 0.0
        self._memory_reserved: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def cpu_available(self) -> float:
        return max(0.0, self.cpu_total - self._cpu_reserved)

    @property
    def memory_available(self) -> float:
        return max(0.0, self.memory_total - self._memory_reserved)

    async def reserve(self, cpu: float, memory: float) -> None:
        async with self._lock:
            self._cpu_reserved += cpu
            self._memory_reserved += memory

    async def release(self, cpu: float, memory: float) -> None:
        async with self._lock:
            self._cpu_reserved = max(0.0, self._cpu_reserved - cpu)
            self._memory_reserved = max(0.0, self._memory_reserved - memory)

    def to_dict(self) -> dict:
        return {
            "cpu_total": self.cpu_total,
            "cpu_available": self.cpu_available,
            "memory_total": self.memory_total,
            "memory_available": self.memory_available,
            "cpu_reserved": self._cpu_reserved,
            "memory_reserved": self._memory_reserved,
        }
