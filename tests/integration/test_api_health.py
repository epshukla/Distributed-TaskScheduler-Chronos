"""Integration tests for health endpoints.

Requires running docker compose services.
"""
import pytest

pytestmark = pytest.mark.skipif(
    True, reason="Requires docker compose services"
)


class TestHealthAPI:
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "is_leader" in data
        assert "uptime_seconds" in data

    async def test_readiness_check(self, client):
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert "postgres" in data
        assert "redis" in data
        assert "etcd" in data
