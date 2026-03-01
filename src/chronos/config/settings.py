from functools import lru_cache
from uuid import uuid4

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHRONOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # PostgreSQL
    postgres_url: str = "postgresql+asyncpg://chronos:chronos@localhost:5432/chronos"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # etcd
    etcd_host: str = "localhost"
    etcd_port: int = 2379

    # Master
    master_host: str = "0.0.0.0"
    master_port: int = 8000
    node_id: str = ""
    master_url: str = "http://localhost:8000"

    # Worker
    worker_hostname: str = ""
    worker_cpu_total: float = 4.0
    worker_memory_total: float = 4096.0
    max_concurrent_tasks_per_worker: int = 10

    # Scheduler
    scheduler_interval_seconds: float = 1.0
    scheduler_batch_size: int = 10
    heartbeat_interval_seconds: int = 5
    heartbeat_timeout_seconds: int = 15
    failure_check_interval_seconds: int = 10

    # Docker container execution
    docker_socket: str = "unix:///var/run/docker.sock"
    default_task_timeout: int = 300
    max_container_log_bytes: int = 10240  # 10KB
    image_pull_timeout: int = 120
    container_stop_timeout: int = 10
    auto_detect_resources: bool = True  # Use psutil instead of env vars for resource detection

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    environment: str = "development"

    def model_post_init(self, __context: object) -> None:
        if not self.node_id:
            self.node_id = f"node-{uuid4().hex[:8]}"
        if not self.worker_hostname:
            self.worker_hostname = f"worker-{uuid4().hex[:8]}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
