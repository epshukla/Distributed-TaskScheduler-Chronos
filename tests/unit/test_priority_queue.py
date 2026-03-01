import pytest

from chronos.redis_client.priority_queue import PriorityQueue


class TestPriorityQueue:
    @pytest.fixture
    def queue(self, mock_redis):
        return PriorityQueue(mock_redis, key="test:queue")

    async def test_enqueue_uses_negative_priority(self, queue, mock_redis):
        await queue.enqueue("task-1", priority=50)
        mock_redis.zadd.assert_called_once_with("test:queue", {"task-1": -50})

    async def test_enqueue_high_priority(self, queue, mock_redis):
        await queue.enqueue("task-1", priority=100)
        mock_redis.zadd.assert_called_once_with("test:queue", {"task-1": -100})

    async def test_dequeue_returns_task_id(self, queue, mock_redis):
        mock_redis.zpopmin.return_value = [("task-1", -50.0)]
        result = await queue.dequeue()
        assert result == "task-1"

    async def test_dequeue_empty_returns_none(self, queue, mock_redis):
        mock_redis.zpopmin.return_value = []
        result = await queue.dequeue()
        assert result is None

    async def test_dequeue_batch(self, queue, mock_redis):
        mock_redis.zpopmin.return_value = [
            ("task-1", -100.0),
            ("task-2", -50.0),
        ]
        result = await queue.dequeue_batch(2)
        assert result == ["task-1", "task-2"]

    async def test_remove(self, queue, mock_redis):
        mock_redis.zrem.return_value = 1
        result = await queue.remove("task-1")
        assert result is True

    async def test_remove_nonexistent(self, queue, mock_redis):
        mock_redis.zrem.return_value = 0
        result = await queue.remove("nonexistent")
        assert result is False

    async def test_size(self, queue, mock_redis):
        mock_redis.zcard.return_value = 5
        result = await queue.size()
        assert result == 5

    async def test_contains_true(self, queue, mock_redis):
        mock_redis.zscore.return_value = -50.0
        result = await queue.contains("task-1")
        assert result is True

    async def test_contains_false(self, queue, mock_redis):
        mock_redis.zscore.return_value = None
        result = await queue.contains("task-1")
        assert result is False
