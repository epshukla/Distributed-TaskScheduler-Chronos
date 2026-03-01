import pytest

from chronos.redis_client.heartbeat_store import HeartbeatStore


class TestHeartbeatStore:
    @pytest.fixture
    def store(self, mock_redis):
        return HeartbeatStore(mock_redis)

    async def test_send_heartbeat(self, store, mock_redis):
        payload = {"cpu_available": 2.0, "memory_available": 2048.0}
        await store.send_heartbeat("worker-1", payload, ttl=15)
        mock_redis.set.assert_called_once()
        args = mock_redis.set.call_args
        assert "chronos:worker:worker-1:heartbeat" in args[0]

    async def test_is_alive_true(self, store, mock_redis):
        mock_redis.exists.return_value = 1
        result = await store.is_alive("worker-1")
        assert result is True

    async def test_is_alive_false(self, store, mock_redis):
        mock_redis.exists.return_value = 0
        result = await store.is_alive("worker-1")
        assert result is False

    async def test_get_heartbeat_returns_payload(self, store, mock_redis):
        import json
        payload = {"cpu_available": 2.0}
        mock_redis.get.return_value = json.dumps(payload)
        result = await store.get_heartbeat("worker-1")
        assert result == payload

    async def test_get_heartbeat_returns_none(self, store, mock_redis):
        mock_redis.get.return_value = None
        result = await store.get_heartbeat("worker-1")
        assert result is None
