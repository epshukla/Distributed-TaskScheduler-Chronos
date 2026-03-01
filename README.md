# Chronos-K8s-Scheduler

**Production-grade Distributed Task Scheduler** inspired by **Kubernetes Control Plane** and **Google Borg**.

A scalable, observable, fault-tolerant task scheduling system that executes real workloads inside Docker containers with enforced resource limits, spread scheduling, priority-based preemption, leader election, heartbeat-based failure detection, live log streaming, a real-time dashboard, and Kubernetes-native deployment support.

---

## Features

### Docker Container Execution
- **Real workload execution** -- Every task runs as an isolated Docker container with enforced CPU/memory limits via cgroups
- **Image pull + lifecycle management** -- Pulls images on demand, creates containers with resource constraints, monitors execution, captures logs
- **Live log streaming** -- Server-Sent Events (SSE) endpoint streams container stdout/stderr in real time
- **OOM and timeout detection** -- Detects out-of-memory kills and timeout exceeded, surfaces them as structured events
- **Orphan container cleanup** -- Workers clean up stale containers from previous runs on startup
- **Task templates** -- Pre-built templates (CPU stress, memory allocator, web scraper, disk I/O, sleep job, fibonacci) for quick demo and testing

### Core Scheduling
- **Spread scheduling (default)** -- Distributes tasks evenly across all available workers by selecting the node with the most remaining resources
- **Best-fit bin-packing (available)** -- Alternative algorithm that minimizes resource fragmentation by selecting the tightest-fitting worker
- **Priority-based preemption** -- Higher-priority tasks evict lower-priority running containers when resources are constrained
- **Task state machine** -- Strict PENDING -> SCHEDULED -> RUNNING -> COMPLETED/FAILED/PREEMPTED/CANCELLED transitions
- **Retry policies** -- Configurable max retries with automatic re-enqueue on failure or preemption
- **Queue reconciliation** -- Startup and periodic reconciliation ensures PENDING tasks in PostgreSQL are always present in the Redis scheduling queue, surviving restarts and crashes

### Distributed Systems
- **Leader election** via etcd leases -- Only the elected master runs the scheduler loop and failure detector
- **Distributed locking** via Redis RedLock -- Prevents duplicate scheduling during leader transitions
- **Heartbeat-based failure detection** -- Workers send TTL-based heartbeats with real resource metrics; expired heartbeats trigger task reassignment
- **Worker pull model** -- Workers poll per-worker Redis lists for assignments (resilient to transient unavailability)
- **Auto-detected resources** -- Workers detect CPU cores and memory via psutil at startup, no manual configuration needed

### Real-Time Dashboard
- **Live WebSocket updates** -- All task state changes, container events, and worker heartbeats push to the browser in real time
- **Task management** -- Submit tasks with Docker image, command, env vars, resource limits; view live logs in a terminal emulator
- **Cluster topology** -- Interactive React Flow visualization showing master, queue, and worker nodes with animated task flow particles
- **Metrics & charts** -- Throughput, CPU utilization, scheduling latency histogram, execution time distribution, exit code breakdown, resource heatmap
- **Event feed** -- Scrollable live feed of all system events with color-coded types

### Observability
- **Prometheus metrics** -- Queue depth, scheduling latency, worker utilization, preemption counts, task state transitions
- **Structured logging** via structlog -- JSON-formatted logs with request IDs, node IDs, and correlation
- **Health and readiness endpoints** -- `/health` and `/ready` with dependency checks
- **Real resource monitoring** -- psutil-based actual CPU/memory usage alongside scheduler-tracked reserved resources

---

## Architecture

```
Client / Dashboard (React + Vite)
        |          |
        | REST     | WebSocket + SSE
        v          v
FastAPI Master (API + Scheduler + Failure Detector + EventBus)
        |            |            |
        v            v            v
    PostgreSQL     Redis        etcd
    (source of    (queue,      (leader
     truth)       locks,       election)
                  heartbeats)
        ^            ^
        |            |
   Worker 1..N (Docker executor + heartbeat + psutil reporter)
        |
        v
   Docker Engine (containers with cgroup resource limits)
```

See [docs/architecture.md](docs/architecture.md) for detailed Mermaid diagrams of all flows.

---

## Tech Stack

| Component | Technology |
|---|---|
| API Server | Python 3.12, FastAPI, uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic |
| Coordination | Redis 7 (sorted sets, lists, locks, TTL keys) |
| Leader Election | etcd 3.5, etcd3-py |
| Container Execution | Docker SDK for Python, Docker Engine |
| Resource Monitoring | psutil (CPU, memory detection and real-time usage) |
| Log Streaming | SSE via sse-starlette |
| Real-Time Events | WebSocket (FastAPI native) |
| Dashboard | React 18, TypeScript, Vite, TailwindCSS, TanStack Query, React Flow, Recharts, Framer Motion |
| Metrics | Prometheus, prometheus-client |
| Logging | structlog (JSON) |
| Testing | pytest, pytest-asyncio, Locust |
| Containerization | Docker, Docker Compose |
| Future Deployment | Helm 3, Kubernetes CRDs, kopf Operator |

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for dashboard development)

### Run with Docker Compose

```bash
# Start all services (master, 3 workers, postgres, redis, etcd, dashboard)
docker compose up -d --build

# Check health
curl http://localhost:8000/health

# Open the real-time dashboard
open http://localhost:5173

# Submit a Docker container task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world",
    "image": "alpine:latest",
    "command": ["echo", "Hello from Chronos!"],
    "priority": 50,
    "resource_cpu": 0.5,
    "resource_memory": 256,
    "max_retries": 3,
    "timeout_seconds": 60
  }'

# Submit a CPU-intensive task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cpu-stress",
    "image": "alpine:latest",
    "command": ["sh", "-c", "dd if=/dev/urandom bs=1M count=100 | md5sum"],
    "priority": 30,
    "resource_cpu": 1.0,
    "resource_memory": 128,
    "timeout_seconds": 120
  }'

# List tasks (with Docker execution details)
curl http://localhost:8000/api/v1/tasks

# Get available task templates
curl http://localhost:8000/api/v1/task-templates

# Stream live container logs (SSE)
curl -N http://localhost:8000/api/v1/tasks/{task_id}/logs?follow=true

# List workers (with real resource metrics)
curl http://localhost:8000/api/v1/workers

# View Prometheus metrics
curl http://localhost:8000/metrics

# View logs
docker compose logs -f master
docker compose logs -f worker-1

# Stop and clean up
docker compose down -v
```

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env

# Run database migrations
alembic upgrade head

# Run master
uvicorn chronos.master.app:create_app --factory --reload

# Run a worker (in another terminal)
python -m chronos.worker.main

# Run dashboard (in another terminal)
cd dashboard && npm install && npm run dev

# Run unit tests
make test-unit

# Run integration tests (requires Docker daemon)
pytest tests/integration/ -m integration

# Run load tests
make load-test
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/tasks` | Submit a new container task |
| `GET` | `/api/v1/tasks/{id}` | Get task details (includes exit code, container ID, logs) |
| `GET` | `/api/v1/tasks` | List tasks (filterable, paginated) |
| `DELETE` | `/api/v1/tasks/{id}` | Cancel a task (stops container if running) |
| `GET` | `/api/v1/tasks/{id}/logs?follow=true` | Stream live container logs (SSE) |
| `GET` | `/api/v1/task-templates` | Get pre-built task templates |
| `GET` | `/api/v1/workers` | List workers (with real resource metrics) |
| `GET` | `/api/v1/workers/{id}` | Get worker details |
| `WS` | `/ws/events` | Real-time system events (WebSocket) |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check (dependency status) |
| `GET` | `/metrics` | Prometheus metrics |

---

## Task Submission Schema

```json
{
  "name": "my-task",
  "image": "python:3.12-slim",
  "command": ["python", "-c", "print('hello')"],
  "args": [],
  "env_vars": {"MY_VAR": "value"},
  "working_dir": "/app",
  "priority": 50,
  "resource_cpu": 1.0,
  "resource_memory": 512,
  "max_retries": 3,
  "timeout_seconds": 300
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Task identifier |
| `image` | string | yes | Docker image to run (e.g. `alpine:latest`) |
| `command` | string[] | no | Container command (overrides ENTRYPOINT) |
| `args` | string[] | no | Command arguments |
| `env_vars` | object | no | Environment variables injected into container |
| `working_dir` | string | no | Working directory inside container |
| `priority` | int | no | 0-100, higher = scheduled first (default: 5) |
| `resource_cpu` | float | no | CPU cores to reserve (default: 0.5) |
| `resource_memory` | float | no | Memory in MB to reserve (default: 256) |
| `max_retries` | int | no | Retry count on failure (default: 3) |
| `timeout_seconds` | int | no | Kill container after N seconds (default: 300) |

---

## Project Structure

```
src/chronos/
  config/          # Pydantic settings, constants
  models/          # SQLAlchemy ORM models (Task, Worker)
  schemas/         # Pydantic request/response schemas
  db/              # Async database engine and sessions
  redis_client/    # Priority queue, heartbeats, locks, assignments
  etcd_client/     # Leader election via etcd leases
  master/
    api/           # FastAPI routes (tasks, workers, health, logs)
    services/      # Business logic layer
    scheduler/     # Scheduler loop, spread/bin-packing, preemption, failure detector
    middleware/     # CORS, logging, and metrics middleware
    events.py      # EventBus (async pub/sub for WebSocket push)
  worker/
    executor.py    # Task executor (dispatches to Docker runner)
    task_runner.py # Docker container lifecycle (pull, create, monitor, capture logs)
    resource_reporter.py  # psutil + Docker stats resource monitoring
    heartbeat.py   # Heartbeat sender with real resource metrics
    main.py        # Worker entry point (auto-detect resources, orphan cleanup)
  metrics/         # Prometheus metric definitions
  state_machine/   # Task state transition validation
  exceptions/      # Custom exception hierarchy
  task_templates.py  # Pre-built task templates for demos

dashboard/         # React + TypeScript real-time dashboard
  src/
    api/           # REST API client functions
    components/    # UI components (tasks, workers, topology, metrics, events)
    hooks/         # React hooks (WebSocket, real-time data, tasks, workers)
    pages/         # Page components (Overview, Tasks, Workers, Metrics, Events)
    providers/     # QueryProvider, WebSocketProvider
    types/         # TypeScript interfaces (Task, Worker, Events)

tests/
  unit/            # Unit tests (no external dependencies)
  integration/     # Docker container execution tests (requires Docker daemon)
```

---

## Testing

```bash
# Unit tests (no external dependencies)
make test-unit

# Integration tests (requires Docker daemon — tests real container execution)
pytest tests/integration/ -m integration

# Load tests
make load-test

# Coverage report
make test-cov
```

### Integration Tests

The integration test suite (`tests/integration/test_docker_execution.py`) validates real Docker container execution:

- Alpine sleep/echo tasks complete successfully
- Non-zero exit codes raise `TaskExecutionError`
- Timeout kills long-running containers
- Bad image names fail gracefully
- Preemption stops running containers
- Environment variables are injected into containers
- CPU/memory resource limits are enforced via cgroups
- Orphan container cleanup works correctly

---

## Worker Cluster

Docker Compose runs 3 workers that auto-detect resources via psutil from the host machine:

| Worker | Resource Detection | Docker Socket |
|---|---|---|
| worker-1 | Auto (psutil) | Mounted |
| worker-2 | Auto (psutil) | Mounted |
| worker-3 | Auto (psutil) | Mounted |

Workers mount `/var/run/docker.sock` to create and manage task containers on the host Docker engine. Resource limits (CPU quota, memory limit) are enforced per container via Docker's cgroup integration.

> **Security note**: Docker socket mounting grants container-level host access. In production, use Docker-in-Docker (DinD) sidecar, rootless Docker, or a dedicated container runtime per worker node.

---

## WebSocket Events

The `/ws/events` WebSocket endpoint pushes real-time events to connected clients:

| Event Type | Trigger |
|---|---|
| `task_created` | New task submitted |
| `task_state_changed` | Task state transition (PENDING -> SCHEDULED -> RUNNING, etc.) |
| `task_scheduled` | Task assigned to a worker by the scheduler |
| `container_started` | Docker container started on a worker |
| `container_exited` | Container exited (includes exit code) |
| `oom_killed` | Container killed due to out-of-memory |
| `timeout_killed` | Container killed due to timeout exceeded |
| `worker_registered` | New worker joined the cluster |
| `worker_heartbeat` | Worker heartbeat with resource metrics |
| `worker_dead` | Worker detected as dead by failure detector |

---

## Future Deployment Scope

### Helm Chart (included skeleton)
- `k8s/helm/chronos-scheduler/` -- Full Helm chart with templates for master (HA), workers (HPA), PostgreSQL, Redis, etcd
- Worker autoscaling via HorizontalPodAutoscaler
- ServiceMonitor for Prometheus Operator integration

### Custom Resource Definitions (included)
- `k8s/crds/task_crd.yaml` -- `kubectl apply -f task.yaml` to submit tasks via K8s API
- `k8s/crds/worker_crd.yaml` -- Declarative worker management

### Kubernetes Operator (included skeleton)
- `k8s/operator/` -- kopf-based operator that reconciles Task/Worker CRDs with the Chronos backend
- Automatic status sync between CRDs and the scheduler
- `kubectl get tasks` / `kubectl get workers` with custom columns

### Multi-Cluster Potential
- Federation via shared etcd or cross-cluster Redis replication
- Worker pools spanning multiple clusters with topology-aware scheduling
- Global priority queue with regional assignment affinity

---

## Key Design Decisions

1. **PostgreSQL = source of truth, Redis = coordination** -- If Redis fails, the scheduler pauses but no data is lost. The queue is reconstructable from the database via automatic reconciliation.
2. **Spread scheduling (default)** -- Distributes tasks evenly across workers by placing each task on the node with the most available resources. Best-fit bin-packing is available as an alternative when resource consolidation is preferred.
3. **Real Docker container execution** -- Every task runs as an isolated Docker container with enforced CPU/memory cgroup limits. Workers manage the full container lifecycle: image pull, create, start, monitor, log capture, cleanup.
4. **Worker pull model** -- Workers poll Redis lists rather than receiving HTTP pushes, naturally handling transient unavailability.
5. **Leader-only background tasks** -- The scheduler loop and failure detector only run on the etcd-elected leader, with RedLock as a safety net.
6. **Queue reconciliation** -- On startup and periodically (~60s), the scheduler reconciles PENDING tasks in PostgreSQL against the Redis queue. Any task missing from Redis is re-enqueued automatically. This ensures no task is lost during restarts, crashes, or Redis failures.
7. **Idempotent worker registration** -- Workers re-register on restart using their hostname as a stable identity. Re-registration resets status to ACTIVE and refreshes resource capacity.
8. **Auto-detected resources** -- Workers use psutil to detect available CPU cores and memory at startup, eliminating manual resource configuration. Real-time usage is reported alongside scheduler-tracked reservations.
9. **EventBus + WebSocket** -- A global async EventBus with per-subscriber bounded queues pushes all system events to the dashboard via WebSocket, with TanStack Query polling as fallback.
10. **SSE log streaming** -- Live container logs are streamed to the dashboard via Server-Sent Events, with stored stdout/stderr available for completed tasks.
