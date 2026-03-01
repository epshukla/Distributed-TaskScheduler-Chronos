import uuid

import pytest

from chronos.exceptions import InvalidStateTransitionError
from chronos.models.enums import TaskState
from chronos.models.task import Task
from chronos.state_machine.transitions import transition_task, validate_transition


class TestValidateTransition:
    def test_pending_to_scheduled(self):
        assert validate_transition(TaskState.PENDING, TaskState.SCHEDULED) is True

    def test_pending_to_cancelled(self):
        assert validate_transition(TaskState.PENDING, TaskState.CANCELLED) is True

    def test_pending_to_running_invalid(self):
        assert validate_transition(TaskState.PENDING, TaskState.RUNNING) is False

    def test_scheduled_to_running(self):
        assert validate_transition(TaskState.SCHEDULED, TaskState.RUNNING) is True

    def test_scheduled_to_pending_reschedule(self):
        assert validate_transition(TaskState.SCHEDULED, TaskState.PENDING) is True

    def test_running_to_completed(self):
        assert validate_transition(TaskState.RUNNING, TaskState.COMPLETED) is True

    def test_running_to_failed(self):
        assert validate_transition(TaskState.RUNNING, TaskState.FAILED) is True

    def test_running_to_preempted(self):
        assert validate_transition(TaskState.RUNNING, TaskState.PREEMPTED) is True

    def test_running_to_cancelled(self):
        assert validate_transition(TaskState.RUNNING, TaskState.CANCELLED) is True

    def test_completed_is_terminal(self):
        assert validate_transition(TaskState.COMPLETED, TaskState.PENDING) is False
        assert validate_transition(TaskState.COMPLETED, TaskState.RUNNING) is False

    def test_cancelled_is_terminal(self):
        assert validate_transition(TaskState.CANCELLED, TaskState.PENDING) is False

    def test_failed_to_pending_retry(self):
        assert validate_transition(TaskState.FAILED, TaskState.PENDING) is True

    def test_preempted_to_pending_requeue(self):
        assert validate_transition(TaskState.PREEMPTED, TaskState.PENDING) is True


class TestTransitionTask:
    def _make_task(self, state: TaskState) -> Task:
        return Task(
            id=uuid.uuid4(),
            name="test",
            priority=10,
            state=state.value,
            resource_cpu=1.0,
            resource_memory=256.0,
        )

    def test_transition_sets_state(self):
        task = self._make_task(TaskState.PENDING)
        transition_task(task, TaskState.SCHEDULED)
        assert task.state == TaskState.SCHEDULED

    def test_transition_sets_scheduled_at(self):
        task = self._make_task(TaskState.PENDING)
        transition_task(task, TaskState.SCHEDULED)
        assert task.scheduled_at is not None

    def test_transition_to_running_sets_started_at(self):
        task = self._make_task(TaskState.SCHEDULED)
        transition_task(task, TaskState.RUNNING)
        assert task.started_at is not None

    def test_transition_to_completed_sets_completed_at(self):
        task = self._make_task(TaskState.RUNNING)
        transition_task(task, TaskState.COMPLETED)
        assert task.completed_at is not None

    def test_transition_sets_error(self):
        task = self._make_task(TaskState.RUNNING)
        transition_task(task, TaskState.FAILED, error="OOM killed")
        assert task.error == "OOM killed"

    def test_transition_sets_result(self):
        task = self._make_task(TaskState.RUNNING)
        result = {"rows": 100}
        transition_task(task, TaskState.COMPLETED, result=result)
        assert task.result == result

    def test_invalid_transition_raises(self):
        task = self._make_task(TaskState.PENDING)
        with pytest.raises(InvalidStateTransitionError):
            transition_task(task, TaskState.RUNNING)

    def test_terminal_state_raises(self):
        task = self._make_task(TaskState.COMPLETED)
        with pytest.raises(InvalidStateTransitionError):
            transition_task(task, TaskState.PENDING)
