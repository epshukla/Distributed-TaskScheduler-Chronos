import pytest

from chronos.worker.resource_reporter import ResourceReporter


class TestResourceReporter:
    def test_initial_state(self):
        rr = ResourceReporter(cpu_total=4.0, memory_total=4096.0)
        assert rr.cpu_available == 4.0
        assert rr.memory_available == 4096.0

    async def test_reserve(self):
        rr = ResourceReporter(cpu_total=4.0, memory_total=4096.0)
        await rr.reserve(2.0, 1024.0)
        assert rr.cpu_available == 2.0
        assert rr.memory_available == 3072.0

    async def test_release(self):
        rr = ResourceReporter(cpu_total=4.0, memory_total=4096.0)
        await rr.reserve(2.0, 1024.0)
        await rr.release(1.0, 512.0)
        assert rr.cpu_available == 3.0
        assert rr.memory_available == 3584.0

    async def test_no_negative_available(self):
        rr = ResourceReporter(cpu_total=4.0, memory_total=4096.0)
        await rr.reserve(5.0, 5000.0)
        assert rr.cpu_available == 0.0
        assert rr.memory_available == 0.0

    async def test_release_beyond_total(self):
        rr = ResourceReporter(cpu_total=4.0, memory_total=4096.0)
        await rr.release(2.0, 1024.0)
        # Should not go negative on reserved
        assert rr.cpu_available == 4.0

    def test_to_dict(self):
        rr = ResourceReporter(cpu_total=4.0, memory_total=4096.0)
        d = rr.to_dict()
        assert d["cpu_total"] == 4.0
        assert d["memory_total"] == 4096.0
        assert d["cpu_available"] == 4.0
