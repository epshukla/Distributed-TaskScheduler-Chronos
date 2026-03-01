import pytest
from pydantic import ValidationError

from chronos.schemas.task import TaskCreate


class TestTaskCreate:
    def test_valid_task(self):
        task = TaskCreate(name="test-task", priority=50)
        assert task.name == "test-task"
        assert task.priority == 50
        assert task.resource_cpu == 1.0
        assert task.resource_memory == 256.0
        assert task.max_retries == 3

    def test_defaults(self):
        task = TaskCreate(name="test")
        assert task.priority == 0
        assert task.duration_seconds == 10.0
        assert task.description is None

    def test_empty_name_invalid(self):
        with pytest.raises(ValidationError):
            TaskCreate(name="")

    def test_priority_range(self):
        TaskCreate(name="t", priority=0)
        TaskCreate(name="t", priority=100)
        with pytest.raises(ValidationError):
            TaskCreate(name="t", priority=-1)
        with pytest.raises(ValidationError):
            TaskCreate(name="t", priority=101)

    def test_resource_cpu_must_be_positive(self):
        with pytest.raises(ValidationError):
            TaskCreate(name="t", resource_cpu=0)
        with pytest.raises(ValidationError):
            TaskCreate(name="t", resource_cpu=-1)

    def test_resource_memory_must_be_positive(self):
        with pytest.raises(ValidationError):
            TaskCreate(name="t", resource_memory=0)

    def test_max_retries_range(self):
        TaskCreate(name="t", max_retries=0)
        TaskCreate(name="t", max_retries=10)
        with pytest.raises(ValidationError):
            TaskCreate(name="t", max_retries=-1)
        with pytest.raises(ValidationError):
            TaskCreate(name="t", max_retries=11)

    def test_duration_must_be_positive(self):
        with pytest.raises(ValidationError):
            TaskCreate(name="t", duration_seconds=0)
        with pytest.raises(ValidationError):
            TaskCreate(name="t", duration_seconds=-5)

    def test_full_valid_task(self):
        task = TaskCreate(
            name="data-processing",
            description="Process batch",
            priority=75,
            resource_cpu=4.0,
            resource_memory=2048.0,
            max_retries=5,
            duration_seconds=120.0,
        )
        assert task.resource_cpu == 4.0
        assert task.description == "Process batch"
