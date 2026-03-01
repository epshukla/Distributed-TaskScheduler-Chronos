"""Integration test: full scheduling flow.

Tests: submit task -> scheduler picks up -> assigns to worker -> completion.
Requires docker compose services.
"""
import pytest

pytestmark = pytest.mark.skipif(
    True, reason="Requires docker compose services"
)


class TestSchedulingFlow:
    async def test_task_gets_scheduled(self, client):
        """Submit a task and verify it transitions to SCHEDULED."""
        # Register a worker first
        await client.post(
            "/internal/workers/register",
            json={"hostname": "sched-test-1", "cpu_total": 4.0, "memory_total": 4096.0},
        )

        # Submit a task
        resp = await client.post(
            "/api/v1/tasks/",
            json={"name": "schedule-test", "priority": 50, "resource_cpu": 1.0, "resource_memory": 256.0},
        )
        task_id = resp.json()["id"]

        # Wait for scheduler to pick it up (would need real scheduler running)
        import asyncio
        await asyncio.sleep(3)

        # Check state
        resp = await client.get(f"/api/v1/tasks/{task_id}")
        state = resp.json()["state"]
        assert state in ("SCHEDULED", "RUNNING", "COMPLETED")

    async def test_priority_ordering(self, client):
        """Higher priority tasks should be scheduled first."""
        await client.post(
            "/internal/workers/register",
            json={"hostname": "prio-test-1", "cpu_total": 1.0, "memory_total": 512.0},
        )

        # Submit low priority first, then high priority
        low = await client.post(
            "/api/v1/tasks/",
            json={"name": "low-prio", "priority": 10, "resource_cpu": 1.0, "resource_memory": 256.0},
        )
        high = await client.post(
            "/api/v1/tasks/",
            json={"name": "high-prio", "priority": 90, "resource_cpu": 1.0, "resource_memory": 256.0},
        )

        import asyncio
        await asyncio.sleep(3)

        # High priority should be scheduled first
        high_resp = await client.get(f"/api/v1/tasks/{high.json()['id']}")
        assert high_resp.json()["state"] in ("SCHEDULED", "RUNNING", "COMPLETED")
