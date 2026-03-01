from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from chronos.exceptions.base import ChronosError
from chronos.exceptions.scheduling_errors import InsufficientResourcesError
from chronos.exceptions.task_errors import (
    InvalidStateTransitionError,
    TaskAlreadyCancelledError,
    TaskNotFoundError,
)
from chronos.exceptions.worker_errors import WorkerNotFoundError, WorkerUnavailableError

_STATUS_MAP: dict[type[ChronosError], int] = {
    TaskNotFoundError: 404,
    WorkerNotFoundError: 404,
    InvalidStateTransitionError: 409,
    TaskAlreadyCancelledError: 409,
    WorkerUnavailableError: 503,
    InsufficientResourcesError: 503,
}


async def chronos_error_handler(request: Request, exc: ChronosError) -> JSONResponse:
    status_code = _STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__, "traceback": traceback.format_exc()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ChronosError, chronos_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)  # type: ignore[arg-type]
