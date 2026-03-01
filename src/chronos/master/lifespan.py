import asyncio
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI

from chronos.config.settings import get_settings
from chronos.db.engine import close_db, init_db
from chronos.etcd_client.connection import create_etcd_client
from chronos.etcd_client.leader_election import LeaderElection
from chronos.logging_config.setup import configure_logging
from chronos.master.scheduler.failure_detector import FailureDetector
from chronos.master.scheduler.scheduler_loop import SchedulerLoop
from chronos.metrics.collectors import BUILD_INFO
from chronos.metrics.instrumentator import update_leader_status
from chronos.redis_client.connection import close_redis, init_redis
from chronos.version import __version__

logger = structlog.get_logger(__name__)


async def _run_migrations(database_url: str) -> None:
    """Create all tables using SQLAlchemy metadata (auto-migration on startup)."""
    from chronos.db.engine import get_engine
    from chronos.models.base import Base
    # Ensure all models are imported so metadata is populated
    import chronos.models.task  # noqa: F401
    import chronos.models.worker  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)

    logger.info("starting_chronos_master", node_id=settings.node_id)
    app.state.start_time = time.time()
    app.state.node_id = settings.node_id

    BUILD_INFO.info({"version": __version__, "node_id": settings.node_id})

    # Initialize database
    db_factory = await init_db(settings.postgres_url)
    app.state.db_factory = db_factory

    # Run migrations on startup
    await _run_migrations(settings.postgres_url)
    logger.info("database_migrations_applied")

    # Initialize Redis
    redis = await init_redis(settings.redis_url)
    app.state.redis = redis

    # Initialize etcd and leader election
    background_tasks: list[asyncio.Task] = []  # type: ignore[type-arg]
    try:
        etcd_client = create_etcd_client(settings.etcd_host, settings.etcd_port)
        app.state.etcd_client = etcd_client

        leader_election = LeaderElection(etcd_client, settings.node_id)
        app.state.leader_election = leader_election
        app.state.is_leader = False

        # Start leader election campaign
        election_task = asyncio.create_task(leader_election.campaign())
        background_tasks.append(election_task)

        # Wait briefly for election to settle
        await asyncio.sleep(3)
        app.state.is_leader = leader_election.is_leader
        update_leader_status(leader_election.is_leader)

        # Keep app.state.is_leader in sync with the election object
        async def _sync_leader_status() -> None:
            while True:
                try:
                    app.state.is_leader = leader_election.is_leader
                    update_leader_status(leader_election.is_leader)
                except asyncio.CancelledError:
                    return
                await asyncio.sleep(2)

        sync_task = asyncio.create_task(_sync_leader_status())
        background_tasks.append(sync_task)

    except Exception as e:
        logger.warning("etcd_unavailable_standalone_mode", error=str(e))
        app.state.etcd_client = None
        app.state.is_leader = True  # standalone mode
        leader_election = None
        update_leader_status(True)

    # Start scheduler loop
    scheduler = SchedulerLoop(
        db_factory=db_factory,
        redis=redis,
        leader_election=leader_election,
        settings=settings,
    )
    scheduler_task = asyncio.create_task(scheduler.run())
    background_tasks.append(scheduler_task)

    # Start failure detector
    failure_detector = FailureDetector(
        db_factory=db_factory,
        redis=redis,
        leader_election=leader_election,
        settings=settings,
    )
    detector_task = asyncio.create_task(failure_detector.run())
    background_tasks.append(detector_task)

    logger.info(
        "chronos_master_started",
        node_id=settings.node_id,
        is_leader=app.state.is_leader,
    )

    yield

    # Shutdown
    logger.info("shutting_down_chronos_master")
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

    if leader_election:
        await leader_election.resign()

    await close_redis()
    await close_db()
    logger.info("chronos_master_stopped")
