"""Integration tests for worker API endpoints.

Requires running docker compose services.
"""
import pytest

pytestmark = pytest.mark.skipif(
    True, reason="Requires docker compose services"
)


class TestWorkerAPI:
    async def test_register_worker(self, client):
        response = await client.post(
            "/internal/workers/register",
            json={
                "hostname": "test-worker-1",
                "cpu_total": 4.0,
                "memory_total": 4096.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["hostname"] == "test-worker-1"
        assert data["status"] == "ACTIVE"

    async def test_list_workers(self, client):
        await client.post(
            "/internal/workers/register",
            json={"hostname": "list-test-1", "cpu_total": 2.0, "memory_total": 2048.0},
        )
        response = await client.get("/api/v1/workers/")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    async def test_worker_heartbeat(self, client):
        reg_resp = await client.post(
            "/internal/workers/register",
            json={"hostname": "hb-test-1", "cpu_total": 4.0, "memory_total": 4096.0},
        )
        worker_id = reg_resp.json()["id"]
        response = await client.post(
            f"/internal/workers/{worker_id}/heartbeat",
            json={"cpu_available": 2.0, "memory_available": 2048.0},
        )
        assert response.status_code == 204
