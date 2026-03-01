from fastapi import APIRouter

from chronos.master.api.health import router as health_router
from chronos.master.api.logs import router as logs_router
from chronos.master.api.tasks import router as tasks_router
from chronos.master.api.workers import (
    internal_router,
    internal_tasks_router,
    router as workers_router,
)


def create_api_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(health_router)
    api_router.include_router(tasks_router)
    api_router.include_router(workers_router)
    api_router.include_router(logs_router)
    api_router.include_router(internal_router)
    api_router.include_router(internal_tasks_router)
    return api_router
