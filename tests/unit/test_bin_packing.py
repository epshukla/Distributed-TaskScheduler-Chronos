import pytest

from chronos.master.scheduler.bin_packing import (
    ResourceRequest,
    WorkerCapacity,
    best_fit_schedule,
    first_fit_schedule,
    spread_schedule,
)


class TestBestFitSchedule:
    def test_single_worker_fits(self):
        workers = [WorkerCapacity("w1", "host-1", 4.0, 4096.0)]
        result = best_fit_schedule(ResourceRequest(2.0, 1024.0), workers)
        assert result is not None
        assert result.worker_id == "w1"

    def test_no_worker_fits(self):
        workers = [WorkerCapacity("w1", "host-1", 1.0, 512.0)]
        result = best_fit_schedule(ResourceRequest(2.0, 1024.0), workers)
        assert result is None

    def test_empty_workers(self):
        result = best_fit_schedule(ResourceRequest(1.0, 256.0), [])
        assert result is None

    def test_best_fit_selects_tightest(self):
        workers = [
            WorkerCapacity("w1", "host-1", 8.0, 8192.0),  # lots of slack
            WorkerCapacity("w2", "host-2", 2.5, 600.0),   # tight fit
            WorkerCapacity("w3", "host-3", 4.0, 4096.0),  # medium
        ]
        result = best_fit_schedule(ResourceRequest(2.0, 512.0), workers)
        assert result is not None
        assert result.worker_id == "w2"  # tightest fit

    def test_exact_fit(self):
        workers = [
            WorkerCapacity("w1", "host-1", 4.0, 4096.0),
            WorkerCapacity("w2", "host-2", 2.0, 512.0),  # exact match
        ]
        result = best_fit_schedule(ResourceRequest(2.0, 512.0), workers)
        assert result is not None
        assert result.worker_id == "w2"

    def test_cpu_too_small(self):
        workers = [WorkerCapacity("w1", "host-1", 1.0, 8192.0)]
        result = best_fit_schedule(ResourceRequest(2.0, 256.0), workers)
        assert result is None

    def test_memory_too_small(self):
        workers = [WorkerCapacity("w1", "host-1", 8.0, 128.0)]
        result = best_fit_schedule(ResourceRequest(1.0, 256.0), workers)
        assert result is None

    def test_deterministic_tie_breaking(self):
        workers = [
            WorkerCapacity("w2", "host-2", 3.0, 1024.0),
            WorkerCapacity("w1", "host-1", 3.0, 1024.0),
        ]
        result = best_fit_schedule(ResourceRequest(1.0, 256.0), workers)
        assert result is not None
        assert result.worker_id == "w1"  # lower ID wins tie


class TestSpreadSchedule:
    def test_spread_selects_most_headroom(self):
        workers = [
            WorkerCapacity("w1", "host-1", 2.5, 600.0),   # tight
            WorkerCapacity("w2", "host-2", 8.0, 8192.0),  # most headroom
            WorkerCapacity("w3", "host-3", 4.0, 4096.0),  # medium
        ]
        result = spread_schedule(ResourceRequest(2.0, 512.0), workers)
        assert result is not None
        assert result.worker_id == "w2"  # most remaining resources

    def test_spread_distributes_identical_workers(self):
        """When workers have identical capacity, spread should still pick one.
        After placing a task and adjusting capacity, the next call should pick a different worker."""
        workers = [
            WorkerCapacity("w1", "host-1", 4.0, 4096.0),
            WorkerCapacity("w2", "host-2", 4.0, 4096.0),
            WorkerCapacity("w3", "host-3", 4.0, 4096.0),
        ]
        req = ResourceRequest(1.0, 256.0)

        # First placement
        first = spread_schedule(req, workers)
        assert first is not None
        # Simulate resource deduction
        first.cpu_available -= req.cpu
        first.memory_available -= req.memory

        # Second placement should pick a different worker
        second = spread_schedule(req, workers)
        assert second is not None
        assert second.worker_id != first.worker_id

    def test_spread_no_worker_fits(self):
        workers = [WorkerCapacity("w1", "host-1", 1.0, 512.0)]
        result = spread_schedule(ResourceRequest(2.0, 1024.0), workers)
        assert result is None

    def test_spread_empty_workers(self):
        result = spread_schedule(ResourceRequest(1.0, 256.0), [])
        assert result is None

    def test_spread_single_worker(self):
        workers = [WorkerCapacity("w1", "host-1", 4.0, 4096.0)]
        result = spread_schedule(ResourceRequest(1.0, 256.0), workers)
        assert result is not None
        assert result.worker_id == "w1"


class TestFirstFitSchedule:
    def test_first_fit_returns_first_match(self):
        workers = [
            WorkerCapacity("w1", "host-1", 4.0, 4096.0),
            WorkerCapacity("w2", "host-2", 2.0, 2048.0),
        ]
        result = first_fit_schedule(ResourceRequest(1.0, 256.0), workers)
        assert result is not None
        assert result.worker_id == "w1"

    def test_first_fit_skips_insufficient(self):
        workers = [
            WorkerCapacity("w1", "host-1", 0.5, 128.0),  # too small
            WorkerCapacity("w2", "host-2", 4.0, 4096.0),
        ]
        result = first_fit_schedule(ResourceRequest(1.0, 256.0), workers)
        assert result is not None
        assert result.worker_id == "w2"

    def test_first_fit_no_match(self):
        workers = [WorkerCapacity("w1", "host-1", 0.5, 128.0)]
        result = first_fit_schedule(ResourceRequest(1.0, 256.0), workers)
        assert result is None
