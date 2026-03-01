from fastapi import FastAPI

from chronos.exceptions.handlers import register_exception_handlers
from chronos.master.api.router import create_api_router
from chronos.master.api.websocket import router as ws_router
from chronos.master.lifespan import lifespan
from chronos.master.middleware.cors import setup_cors
from chronos.master.middleware.logging_middleware import LoggingMiddleware
from chronos.master.middleware.metrics_middleware import setup_metrics
from chronos.version import __version__


def create_app() -> FastAPI:
    app = FastAPI(
        title="Chronos-K8s-Scheduler",
        description="Production-grade Distributed Task Scheduler inspired by Kubernetes + Borg",
        version=__version__,
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # CORS (must be before other middleware)
    setup_cors(app)

    # Middleware
    app.add_middleware(LoggingMiddleware)

    # Routes
    app.include_router(create_api_router())
    app.include_router(ws_router)

    # Exception handlers
    register_exception_handlers(app)

    # Prometheus metrics
    setup_metrics(app)

    return app
