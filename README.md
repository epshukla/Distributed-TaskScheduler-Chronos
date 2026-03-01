# Chronos-K8s-Scheduler

**Production-grade Distributed Task Scheduler** inspired by **Kubernetes Control Plane** and **Google Borg**.

A scalable, observable, fault-tolerant task scheduling system with resource-aware bin-packing, priority-based preemption, leader election, heartbeat-based failure detection, and Kubernetes-native deployment support.

---

## Features

### Core Scheduling
- **Resource-aware bin-packing** -- Best-fit algorithm minimizes resource fragmentation across heterogeneous workers
- **Priority-based preemption** -- Higher-priority tasks evict lower-priority running tasks when resources are constrained
- **Task state machine** -- Strict PENDING -> SCHEDULED -> RUNNING -> COMPLETED/FAILED/PREEMPTED/CANCELLED transitions
- **Retry policies** -- Configurable max retries with automatic re-enqueue on failure or preemption
- **Queue reconciliation** -- Startup and periodic reconciliation ensures PENDING tasks in PostgreSQL are always present in the Redis scheduling queue, surviving restarts and crashes

### Distributed Systems
- **Leader election** via etcd leases -- Only the elected master runs the scheduler loop and failure detector
- **Distributed locking** via Redis RedLock -- Prevents duplicate scheduling during leader transitions
- **Heartbeat-based failure detection** -- Workers send TTL-based heartbeats; expired heartbeats trigger task reassignment
- **Worker pull model** -- Workers poll per-worker Redis lists for assignments (resilient to transient unavailability)

### Observability
- **Prometheus metrics** -- Queue depth, scheduling latency, worker utilization, preemption counts, task state transitions
- **Structured logging** via structlog -- JSON-formatted logs with request IDs, node IDs, and correlation
- **Health and readiness endpoints** -- `/health` and `/ready` with dependency checks

### API
- RESTful task submission, listing, cancellation
- Worker registration and heartbeat endpoints
- Paginated, filterable task queries

---

## Architecture

```
Client --> FastAPI Master (API + Scheduler + Failure Detector)
               |            |            |
               v            v            v
           PostgreSQL     Redis        etcd
           (source of    (queue,      (leader
            truth)       locks,       election)
                         heartbeats)
               ^            ^
               |            |
          Worker 1..N (executor + heartbeat sender)
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
| Workers | asyncio-based Python processes |
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

### Run with Docker Compose

```bash
# Start all services (master, 5 workers, postgres, redis, etcd)
docker compose up -d --build

# Check health
curl http://localhost:8000/health

# Submit a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-processing-job",
    "priority": 50,
    "resource_cpu": 2.0,
    "resource_memory": 512.0,
    "max_retries": 3,
    "duration_seconds": 15.0
  }'

# List tasks
curl http://localhost:8000/api/v1/tasks

# List workers
curl http://localhost:8000/api/v1/workers

# View metrics
curl http://localhost:8000/metrics

# View logs
docker compose logs -f master
docker compose logs -f worker-1

# Stop
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

# Run tests
make test

# Run load tests
make load-test
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/tasks` | Submit a new task |
| `GET` | `/api/v1/tasks/{id}` | Get task details |
| `GET` | `/api/v1/tasks` | List tasks (filterable, paginated) |
| `DELETE` | `/api/v1/tasks/{id}` | Cancel a task |
| `GET` | `/api/v1/workers` | List workers |
| `GET` | `/api/v1/workers/{id}` | Get worker details |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check (dependency status) |
| `GET` | `/metrics` | Prometheus metrics |

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
    api/           # FastAPI routes (tasks, workers, health)
    services/      # Business logic layer
    scheduler/     # Scheduler loop, bin-packing, preemption, failure detector
    middleware/     # Logging and metrics middleware
  worker/          # Worker executor, heartbeat sender, task runner
  metrics/         # Prometheus metric definitions
  state_machine/   # Task state transition validation
  exceptions/      # Custom exception hierarchy
```

---

## Testing

```bash
# Unit tests (no external dependencies)
make test-unit

# Integration tests (requires docker compose services)
make test-integration

# Load tests
make load-test

# Coverage report
make test-cov
```

---

## Heterogeneous Worker Cluster

The Docker Compose setup includes 5 workers with varying resources to exercise bin-packing:

| Worker | CPU | Memory | Profile |
|---|---|---|---|
| worker-1 | 4 cores | 4 GB | Standard |
| worker-2 | 4 cores | 4 GB | Standard |
| worker-3 | 2 cores | 2 GB | Small |
| worker-4 | 2 cores | 2 GB | Small |
| worker-5 | 8 cores | 8 GB | Large |

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
2. **Best-fit bin-packing** -- Minimizes resource fragmentation by placing tasks on the tightest-fitting worker.
3. **Worker pull model** -- Workers poll Redis lists rather than receiving HTTP pushes, naturally handling transient unavailability.
4. **Leader-only background tasks** -- The scheduler loop and failure detector only run on the etcd-elected leader, with RedLock as a safety net.
5. **Queue reconciliation** -- On startup and periodically (~60s), the scheduler reconciles PENDING tasks in PostgreSQL against the Redis queue. Any task missing from Redis is re-enqueued automatically. This ensures no task is lost during restarts, crashes, or Redis failures.
6. **Idempotent worker registration** -- Workers re-register on restart using their hostname as a stable identity. Re-registration resets status to ACTIVE and refreshes resource capacity.
7. **Simulated workloads** -- Task execution is simulated via `asyncio.sleep()` to demonstrate the scheduling framework. The `task_runner.py` module is designed for easy replacement with real execution logic.
