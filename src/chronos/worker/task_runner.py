import asyncio
import time

import docker
import docker.errors
import structlog

from chronos.config.settings import get_settings

logger = structlog.get_logger(__name__)


class TaskPreemptedError(Exception):
    pass


class TaskExecutionError(Exception):
    pass


async def run_task(
    task_id: str,
    task_data: dict,
    cancel_event: asyncio.Event,
    worker_id: str = "",
) -> dict:
    """Execute a task inside a Docker container with enforced resource limits.

    Pulls the image, creates and starts a container, monitors it for
    completion/timeout/preemption, captures logs, and returns results.
    """
    settings = get_settings()
    image = task_data.get("image", "alpine:latest")
    command = task_data.get("command")
    args = task_data.get("args")
    env_vars = task_data.get("env_vars") or {}
    working_dir = task_data.get("working_dir")
    timeout_seconds = task_data.get("timeout_seconds", settings.default_task_timeout)
    resource_cpu = task_data.get("resource_cpu", 1.0)
    resource_memory = task_data.get("resource_memory", 256)
    name = task_data.get("name", "unknown")
    max_log_bytes = settings.max_container_log_bytes

    # Build full command
    full_command = None
    if command:
        full_command = list(command)
        if args:
            full_command.extend(args)

    logger.info(
        "task_execution_started",
        task_id=task_id,
        name=name,
        image=image,
        command=full_command,
        timeout=timeout_seconds,
    )

    # Connect to Docker daemon
    try:
        client = docker.from_env()
        client.ping()
    except Exception as e:
        raise TaskExecutionError(f"Cannot connect to Docker daemon: {e}") from e

    # Pull image if not present locally
    try:
        client.images.get(image)
        logger.debug("image_already_present", image=image)
    except docker.errors.ImageNotFound:
        logger.info("pulling_image", image=image, task_id=task_id)
        try:
            client.images.pull(image)
            logger.info("image_pulled", image=image, task_id=task_id)
        except docker.errors.APIError as e:
            raise TaskExecutionError(f"Failed to pull image '{image}': {e}") from e
        except Exception as e:
            raise TaskExecutionError(f"Image pull error for '{image}': {e}") from e

    # Check for preemption before container creation
    if cancel_event.is_set():
        logger.info("task_preempted_before_start", task_id=task_id)
        raise TaskPreemptedError(f"Task {task_id} was preempted before container start")

    # Create and start container with resource limits
    container = None
    try:
        # Convert CPU cores to Docker cpu_quota (1.0 core = period 100000, quota 100000)
        cpu_period = 100000
        cpu_quota = int(resource_cpu * cpu_period)
        mem_limit = f"{int(resource_memory)}m"

        container_kwargs: dict = {
            "image": image,
            "detach": True,
            "auto_remove": False,
            "labels": {
                "chronos.task_id": task_id,
                "chronos.worker_id": worker_id,
                "chronos.task_name": name,
            },
            "cpu_period": cpu_period,
            "cpu_quota": cpu_quota,
            "mem_limit": mem_limit,
            "network_mode": "bridge",
            "environment": env_vars,
        }

        if full_command:
            container_kwargs["command"] = full_command
        if working_dir:
            container_kwargs["working_dir"] = working_dir

        container = client.containers.run(**container_kwargs)
        container_id = container.id
        logger.info(
            "container_started",
            task_id=task_id,
            container_id=container_id[:12],
            image=image,
        )

    except docker.errors.APIError as e:
        raise TaskExecutionError(f"Failed to create/start container: {e}") from e
    except Exception as e:
        raise TaskExecutionError(f"Container creation error: {e}") from e

    # Monitor container in a loop
    start_time = time.monotonic()
    check_interval = 0.5

    try:
        while True:
            # Check for preemption
            if cancel_event.is_set():
                logger.info("task_preempted_stopping_container", task_id=task_id)
                try:
                    container.stop(timeout=settings.container_stop_timeout)
                except Exception:
                    try:
                        container.kill()
                    except Exception:
                        pass
                _safe_remove(container)
                raise TaskPreemptedError(f"Task {task_id} was preempted")

            # Check timeout
            elapsed = time.monotonic() - start_time
            if elapsed > timeout_seconds:
                logger.warning(
                    "task_timeout_killing_container",
                    task_id=task_id,
                    elapsed=round(elapsed, 1),
                    timeout=timeout_seconds,
                )
                try:
                    container.kill()
                except Exception:
                    pass
                # Capture logs before removal
                stdout_logs, stderr_logs = _capture_logs(container, max_log_bytes)
                _safe_remove(container)
                raise TaskExecutionError(
                    f"Timeout exceeded: task ran for {elapsed:.0f}s (limit: {timeout_seconds}s)"
                )

            # Check container status
            try:
                container.reload()
            except docker.errors.NotFound:
                # Container disappeared (auto-removed or crashed hard)
                break

            status = container.status
            if status in ("exited", "dead"):
                break

            await asyncio.sleep(check_interval)

    except (TaskPreemptedError, TaskExecutionError):
        raise
    except Exception as e:
        # Unexpected error during monitoring — clean up container
        if container:
            try:
                container.kill()
            except Exception:
                pass
            _safe_remove(container)
        raise TaskExecutionError(f"Error monitoring container: {e}") from e

    # Container has exited — gather results
    duration = time.monotonic() - start_time

    try:
        # Get exit code
        container.reload()
        exit_info = container.attrs.get("State", {})
        exit_code = exit_info.get("ExitCode", -1)
        oom_killed = exit_info.get("OOMKilled", False)

        # Capture logs
        stdout_logs, stderr_logs = _capture_logs(container, max_log_bytes)

        # Clean up container
        _safe_remove(container)

        if oom_killed:
            raise TaskExecutionError(
                f"OOM Killed: container exceeded memory limit of {resource_memory}MB"
            )

        result = {
            "task_id": task_id,
            "name": name,
            "exit_code": exit_code,
            "stdout": stdout_logs,
            "stderr": stderr_logs,
            "container_id": container_id,
            "duration_actual": round(duration, 2),
            "image": image,
            "status": "completed" if exit_code == 0 else "failed",
        }

        if exit_code != 0:
            error_msg = stderr_logs[:500] if stderr_logs else f"Container exited with code {exit_code}"
            logger.warning(
                "task_nonzero_exit",
                task_id=task_id,
                exit_code=exit_code,
                error=error_msg[:200],
            )
            raise TaskExecutionError(
                f"Container exited with code {exit_code}: {error_msg}"
            )

        logger.info(
            "task_execution_completed",
            task_id=task_id,
            exit_code=exit_code,
            duration=round(duration, 2),
        )
        return result

    except (TaskExecutionError, TaskPreemptedError):
        raise
    except docker.errors.NotFound:
        # Container was already removed
        return {
            "task_id": task_id,
            "name": name,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "container_id": container_id,
            "duration_actual": round(duration, 2),
            "image": image,
            "status": "completed",
        }
    except Exception as e:
        _safe_remove(container)
        raise TaskExecutionError(f"Error reading container results: {e}") from e


def _capture_logs(container: "docker.models.containers.Container", max_bytes: int) -> tuple[str, str]:
    """Capture the last max_bytes of stdout and stderr from a container."""
    try:
        stdout_raw = container.logs(stdout=True, stderr=False, tail=500)
        stderr_raw = container.logs(stdout=False, stderr=True, tail=500)
        stdout = stdout_raw.decode("utf-8", errors="replace")[-max_bytes:] if stdout_raw else ""
        stderr = stderr_raw.decode("utf-8", errors="replace")[-max_bytes:] if stderr_raw else ""
        return stdout, stderr
    except Exception as e:
        logger.warning("log_capture_failed", error=str(e))
        return "", ""


def _safe_remove(container: "docker.models.containers.Container") -> None:
    """Remove a container, ignoring errors if already removed."""
    try:
        container.remove(force=True)
    except Exception:
        pass


def cleanup_orphaned_containers(worker_id: str) -> int:
    """Clean up any orphaned Chronos containers from a previous worker run.

    Called on worker startup to ensure no stale containers remain.
    Returns the number of containers cleaned up.
    """
    try:
        client = docker.from_env()
        containers = client.containers.list(
            all=True,
            filters={"label": f"chronos.worker_id={worker_id}"},
        )
        cleaned = 0
        for container in containers:
            try:
                logger.info(
                    "cleaning_orphaned_container",
                    container_id=container.id[:12],
                    task_id=container.labels.get("chronos.task_id", "unknown"),
                )
                container.remove(force=True)
                cleaned += 1
            except Exception as e:
                logger.warning("orphan_cleanup_failed", container_id=container.id[:12], error=str(e))
        return cleaned
    except Exception as e:
        logger.warning("orphan_cleanup_error", error=str(e))
        return 0
