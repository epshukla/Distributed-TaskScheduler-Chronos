"""Chronos Kubernetes Operator

Watches Task and Worker CRDs and reconciles them with the
Chronos scheduler backend (master API).
"""
import logging
import os

import httpx
import kopf

MASTER_URL = os.environ.get("CHRONOS_MASTER_URL", "http://chronos-master:8000")
logger = logging.getLogger("chronos-operator")


# --- Task Handlers ---


@kopf.on.create("chronos.io", "v1alpha1", "tasks")
async def task_created(spec, name, namespace, status, patch, **kwargs):
    """When a Task CRD is created, submit it to the Chronos master API."""
    logger.info(f"Task created: {name} in {namespace}")

    task_data = {
        "name": spec.get("name", name),
        "description": spec.get("description", ""),
        "priority": spec.get("priority", 0),
        "resource_cpu": spec.get("resources", {}).get("cpu", 1.0),
        "resource_memory": spec.get("resources", {}).get("memory", 256),
        "max_retries": spec.get("retryPolicy", {}).get("maxRetries", 3),
        "duration_seconds": spec.get("durationSeconds", 10),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MASTER_URL}/api/v1/tasks", json=task_data)
        response.raise_for_status()
        result = response.json()

    patch.status["state"] = result["state"]
    patch.status["backendTaskId"] = result["id"]
    return {"message": f"Task submitted to Chronos: {result['id']}"}


@kopf.on.delete("chronos.io", "v1alpha1", "tasks")
async def task_deleted(spec, name, namespace, status, **kwargs):
    """When a Task CRD is deleted, cancel the task in the backend."""
    task_id = status.get("backendTaskId")
    if task_id:
        async with httpx.AsyncClient() as client:
            await client.delete(f"{MASTER_URL}/api/v1/tasks/{task_id}")
    logger.info(f"Task deleted: {name}")


@kopf.timer("chronos.io", "v1alpha1", "tasks", interval=10)
async def task_status_sync(spec, name, namespace, status, patch, **kwargs):
    """Periodically sync task status from the backend to the CRD."""
    task_id = status.get("backendTaskId")
    if not task_id:
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MASTER_URL}/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            backend = response.json()
            patch.status["state"] = backend["state"]
            patch.status["assignedWorker"] = backend.get("assigned_worker_id")
            patch.status["retryCount"] = backend.get("retry_count", 0)
            if backend.get("started_at"):
                patch.status["startedAt"] = backend["started_at"]
            if backend.get("completed_at"):
                patch.status["completedAt"] = backend["completed_at"]
            if backend.get("error"):
                patch.status["error"] = backend["error"]


# --- Worker Handlers ---


@kopf.on.create("chronos.io", "v1alpha1", "workers")
async def worker_created(spec, name, namespace, patch, **kwargs):
    """When a Worker CRD is created, register it with the master."""
    logger.info(f"Worker created: {name}")

    worker_data = {
        "hostname": spec.get("hostname", name),
        "cpu_total": spec.get("resources", {}).get("cpuTotal", 4.0),
        "memory_total": spec.get("resources", {}).get("memoryTotal", 4096),
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MASTER_URL}/internal/workers/register", json=worker_data
        )
        response.raise_for_status()
        result = response.json()

    patch.status["phase"] = "Active"
    patch.status["backendWorkerId"] = result["id"]


@kopf.on.delete("chronos.io", "v1alpha1", "workers")
async def worker_deleted(spec, name, namespace, status, **kwargs):
    """When a Worker CRD is deleted, deregister from the backend."""
    logger.info(f"Worker deleted: {name}")


@kopf.timer("chronos.io", "v1alpha1", "workers", interval=15)
async def worker_status_sync(spec, name, namespace, status, patch, **kwargs):
    """Periodically sync worker status from the backend to the CRD."""
    worker_id = status.get("backendWorkerId")
    if not worker_id:
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MASTER_URL}/api/v1/workers/{worker_id}")
        if response.status_code == 200:
            backend = response.json()
            patch.status["phase"] = backend["status"].capitalize()
            patch.status["cpuAvailable"] = backend.get("cpu_available")
            patch.status["memoryAvailable"] = backend.get("memory_available")
            patch.status["lastHeartbeat"] = backend.get("last_heartbeat")


# --- Startup ---


@kopf.on.startup()
async def startup(settings: kopf.OperatorSettings, **kwargs):
    """Configure operator settings."""
    settings.posting.level = logging.WARNING
    settings.watching.server_timeout = 270
    logger.info("Chronos operator started")
