"""Integration tests for task API endpoints.

Requires running docker compose services (postgres, redis, etcd).
Run with: pytest tests/integration/ -v
"""
import pytest
from httpx import ASGITransport, AsyncClient

# Skip if services not available
pytestmark = pytest.mark.skipif(
    True,  # Set to False when running with docker compose
    reason="Requires docker compose services",
)


@pytest.fixture
async def client():
    from chronos.master.app import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestTaskAPI:
    async def test_create_task(self, client):
        response = await client.post(
            "/api/v1/tasks/",
            json={
                "name": "test-task",
                "priority": 50,
                "resource_cpu": 2.0,
                "resource_memory": 512.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-task"
        assert data["state"] == "PENDING"
        assert data["priority"] == 50

    async def test_get_task(self, client):
        create_resp = await client.post(
            "/api/v1/tasks/", json={"name": "get-test"}
        )
        task_id = create_resp.json()["id"]
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id

    async def test_get_task_not_found(self, client):
        import uuid
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/tasks/{fake_id}")
        assert response.status_code == 404

    async def test_list_tasks(self, client):
        for i in range(3):
            await client.post("/api/v1/tasks/", json={"name": f"list-test-{i}"})
        response = await client.get("/api/v1/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert "items" in data

    async def test_list_tasks_filter_by_state(self, client):
        await client.post("/api/v1/tasks/", json={"name": "filter-test"})
        response = await client.get("/api/v1/tasks/?state=PENDING")
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["state"] == "PENDING"

    async def test_cancel_task(self, client):
        create_resp = await client.post(
            "/api/v1/tasks/", json={"name": "cancel-test"}
        )
        task_id = create_resp.json()["id"]
        response = await client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["state"] == "CANCELLED"
