import pytest

from chronos.master.scheduler.bin_packing import (
    ResourceRequest,
    WorkerCapacity,
    best_fit_schedule,
    first_fit_schedule,
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
