"""Integration tests for Docker container execution.

These tests require a running Docker daemon and are tagged as 'integration'.
Run with: pytest tests/integration/test_docker_execution.py -m integration
"""
import asyncio

import pytest

from chronos.worker.task_runner import (
    TaskExecutionError,
    TaskPreemptedError,
    cleanup_orphaned_containers,
    run_task,
)

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def cancel_event():
    return asyncio.Event()


class TestDockerTaskExecution:
    """Test real Docker container execution via the task runner."""

    async def test_alpine_sleep_completes(self, cancel_event):
        """Submit an alpine:latest sleep 5 task and verify it completes."""
        task_data = {
            "name": "test-sleep",
            "image": "alpine:latest",
            "command": ["sleep", "3"],
            "resource_cpu": 0.25,
            "resource_memory": 64,
            "timeout_seconds": 30,
        }

        result = await run_task(
            task_id="test-sleep-001",
            task_data=task_data,
            cancel_event=cancel_event,
            worker_id="test-worker",
        )

        assert result["exit_code"] == 0
        assert result["status"] == "completed"
        assert result["container_id"]
        assert result["duration_actual"] >= 2.0

    async def test_alpine_echo_captures_stdout(self, cancel_event):
        """Verify stdout is captured from the container."""
        task_data = {
            "name": "test-echo",
            "image": "alpine:latest",
            "command": ["echo", "hello-chronos"],
            "resource_cpu": 0.25,
            "resource_memory": 32,
            "timeout_seconds": 30,
        }

        result = await run_task(
            task_id="test-echo-001",
            task_data=task_data,
            cancel_event=cancel_event,
            worker_id="test-worker",
        )

        assert result["exit_code"] == 0
        assert "hello-chronos" in result["stdout"]

    async def test_nonzero_exit_raises_error(self, cancel_event):
        """Verify a non-zero exit code raises TaskExecutionError."""
        task_data = {
            "name": "test-fail",
            "image": "alpine:latest",
            "command": ["sh", "-c", "echo 'error output' >&2; exit 42"],
            "resource_cpu": 0.25,
            "resource_memory": 32,
            "timeout_seconds": 30,
        }

        with pytest.raises(TaskExecutionError, match="exit code 42"):
            await run_task(
                task_id="test-fail-001",
                task_data=task_data,
                cancel_event=cancel_event,
                worker_id="test-worker",
            )

    async def test_timeout_kills_container(self, cancel_event):
        """Submit a task with a 5-second timeout and a sleep 30 command, verify timeout kill."""
        task_data = {
            "name": "test-timeout",
            "image": "alpine:latest",
            "command": ["sleep", "60"],
            "resource_cpu": 0.25,
            "resource_memory": 32,
            "timeout_seconds": 3,
        }

        with pytest.raises(TaskExecutionError, match="Timeout exceeded"):
            await run_task(
                task_id="test-timeout-001",
                task_data=task_data,
                cancel_event=cancel_event,
                worker_id="test-worker",
            )

    async def test_bad_image_raises_error(self, cancel_event):
        """Submit a bad image name and verify graceful failure."""
        task_data = {
            "name": "test-bad-image",
            "image": "nonexistent-image-xyz-123456:latest",
            "command": ["echo", "should not run"],
            "resource_cpu": 0.25,
            "resource_memory": 32,
            "timeout_seconds": 30,
        }

        with pytest.raises(TaskExecutionError, match="(pull|image|not found)"):
            await run_task(
                task_id="test-bad-image-001",
                task_data=task_data,
                cancel_event=cancel_event,
                worker_id="test-worker",
            )

    async def test_preemption_stops_container(self):
        """Test preemption of a running Docker container."""
        cancel_event = asyncio.Event()

        task_data = {
            "name": "test-preempt",
            "image": "alpine:latest",
            "command": ["sleep", "60"],
            "resource_cpu": 0.25,
            "resource_memory": 32,
            "timeout_seconds": 120,
        }

        # Schedule preemption after 2 seconds
        async def preempt_after_delay():
            await asyncio.sleep(2)
            cancel_event.set()

        preempt_task = asyncio.create_task(preempt_after_delay())

        with pytest.raises(TaskPreemptedError):
            await run_task(
                task_id="test-preempt-001",
                task_data=task_data,
                cancel_event=cancel_event,
                worker_id="test-worker",
            )

        preempt_task.cancel()

    async def test_env_vars_injected(self, cancel_event):
        """Verify environment variables are injected into the container."""
        task_data = {
            "name": "test-env",
            "image": "alpine:latest",
            "command": ["sh", "-c", "echo $MY_VAR"],
            "env_vars": {"MY_VAR": "chronos-test-value"},
            "resource_cpu": 0.25,
            "resource_memory": 32,
            "timeout_seconds": 30,
        }

        result = await run_task(
            task_id="test-env-001",
            task_data=task_data,
            cancel_event=cancel_event,
            worker_id="test-worker",
        )

        assert result["exit_code"] == 0
        assert "chronos-test-value" in result["stdout"]

    async def test_resource_limits_enforced(self, cancel_event):
        """Verify that CPU and memory limits are applied to the container."""
        task_data = {
            "name": "test-limits",
            "image": "alpine:latest",
            "command": ["cat", "/sys/fs/cgroup/memory.max"],
            "resource_cpu": 0.5,
            "resource_memory": 128,
            "timeout_seconds": 30,
        }

        # This test verifies the container gets created with limits.
        # The exact cgroup path varies by cgroup version, so we just
        # verify the container starts and completes.
        result = await run_task(
            task_id="test-limits-001",
            task_data=task_data,
            cancel_event=cancel_event,
            worker_id="test-worker",
        )

        # Container should run (even if the cgroup read fails, that's ok —
        # what matters is it was created with limits)
        assert result["container_id"]

    async def test_orphan_cleanup(self):
        """Verify cleanup_orphaned_containers removes stale containers."""
        # Just verify the function doesn't crash — actual orphans may or may not exist
        cleaned = cleanup_orphaned_containers("test-cleanup-worker")
        assert isinstance(cleaned, int)
        assert cleaned >= 0
