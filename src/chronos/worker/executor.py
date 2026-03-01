import asyncio

import httpx
import structlog

from chronos.metrics.collectors import TASK_EXECUTION_DURATION
from chronos.redis_client.task_assignment import TaskAssignmentQueue
from chronos.worker.resource_reporter import ResourceReporter
from chronos.worker.task_runner import TaskExecutionError, TaskPreemptedError, run_task

logger = structlog.get_logger(__name__)


class TaskExecutor:
    """Polls Redis for task assignments and executes them as Docker containers."""

    def __init__(
        self,
        worker_id: str,
        assignment_queue: TaskAssignmentQueue,
        resource_reporter: ResourceReporter,
        master_url: str,
    ):
        self._worker_id = worker_id
        self._assignments = assignment_queue
        self._reporter = resource_reporter
        self._master_url = master_url
        self._running_tasks: dict[str, asyncio.Event] = {}
        self._http_client = httpx.AsyncClient(base_url=master_url, timeout=10.0)

    async def run(self) -> None:
        logger.info("task_executor_started", worker_id=self._worker_id)
        preempt_task = asyncio.create_task(self._preemption_listener())

        try:
            while True:
                try:
                    task_id = await self._assignments.poll_assignment(
                        self._worker_id, timeout=5
                    )
                    if task_id:
                        asyncio.create_task(self._execute_task(task_id))
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("assignment_poll_error", error=str(e))
                    await asyncio.sleep(1)
        finally:
            preempt_task.cancel()
            await self._http_client.aclose()

    async def _execute_task(self, task_id: str) -> None:
        """Fetch task details, run it as a Docker container, report result."""
        cancel_event = asyncio.Event()
        self._running_tasks[task_id] = cancel_event
        task_data: dict | None = None

        try:
            # Fetch task details from master
            task_data = await self._fetch_task(task_id)
            if task_data is None:
                return

            # Reserve resources
            cpu = task_data.get("resource_cpu", 1.0)
            memory = task_data.get("resource_memory", 256.0)
            await self._reporter.reserve(cpu, memory)

            # Track as active
            await self._assignments.add_active_task(self._worker_id, task_id)

            # Report RUNNING state
            await self._report_state(task_id, "RUNNING")

            # Execute Docker container
            import time
            start = time.perf_counter()
            result = await run_task(
                task_id=task_id,
                task_data=task_data,
                cancel_event=cancel_event,
                worker_id=self._worker_id,
            )
            duration = time.perf_counter() - start
            TASK_EXECUTION_DURATION.observe(duration)

            # Report COMPLETED with container execution results
            await self._report_completion(task_id, result)

        except TaskPreemptedError:
            logger.info("task_preempted", task_id=task_id)
            # State already set by master

        except TaskExecutionError as e:
            logger.error("task_failed", task_id=task_id, error=str(e))
            # Extract container results from the error context if available
            await self._report_failure(task_id, str(e))

        except Exception as e:
            logger.error("task_execution_unexpected_error", task_id=task_id, error=str(e))
            await self._report_failure(task_id, str(e))

        finally:
            self._running_tasks.pop(task_id, None)
            await self._assignments.remove_active_task(self._worker_id, task_id)
            if task_data:
                cpu = task_data.get("resource_cpu", 1.0)
                memory = task_data.get("resource_memory", 256.0)
            else:
                cpu = 1.0
                memory = 256.0
            await self._reporter.release(cpu, memory)

    async def _preemption_listener(self) -> None:
        """Listen for preemption signals and cancel running tasks."""
        while True:
            try:
                task_id = await self._assignments.check_preempt_nonblocking(self._worker_id)
                if task_id and task_id in self._running_tasks:
                    logger.info("preemption_signal_received", task_id=task_id)
                    self._running_tasks[task_id].set()
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error("preemption_listener_error", error=str(e))
            await asyncio.sleep(0.5)

    async def _fetch_task(self, task_id: str) -> dict | None:
        try:
            response = await self._http_client.get(f"/api/v1/tasks/{task_id}")
            if response.status_code == 200:
                return response.json()
            logger.error("fetch_task_failed", task_id=task_id, status=response.status_code)
        except Exception as e:
            logger.error("fetch_task_error", task_id=task_id, error=str(e))
        return None

    async def _report_state(self, task_id: str, state: str) -> None:
        try:
            await self._http_client.post(
                f"/internal/tasks/{task_id}/state",
                json={"state": state, "worker_id": self._worker_id},
            )
        except Exception as e:
            logger.error("report_state_error", task_id=task_id, error=str(e))

    async def _report_completion(self, task_id: str, result: dict) -> None:
        try:
            await self._http_client.post(
                f"/internal/tasks/{task_id}/complete",
                json={
                    "result": result,
                    "exit_code": result.get("exit_code"),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "container_id": result.get("container_id", ""),
                },
            )
        except Exception as e:
            logger.error("report_completion_error", task_id=task_id, error=str(e))

    async def _report_failure(self, task_id: str, error: str) -> None:
        try:
            await self._http_client.post(
                f"/internal/tasks/{task_id}/fail",
                json={"error": error},
            )
        except Exception as e:
            logger.error("report_failure_error", task_id=task_id, error=str(e))
