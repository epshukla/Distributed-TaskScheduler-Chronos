# Chronos-K8s-Scheduler Architecture

## System Architecture

```mermaid
graph TB
    subgraph "Clients"
        CLI[CLI / curl]
        UI[Dashboard<br/>React + Vite :5173]
        K8S_API[kubectl + CRDs]
    end

    subgraph "Control Plane"
        subgraph "Master HA (2+ replicas)"
            M1[Master-1<br/>FastAPI + Scheduler + EventBus]
            M2[Master-2<br/>FastAPI standby]
        end
        M1 -.->|leader election| ETCD
        M2 -.->|follower watch| ETCD
    end

    subgraph "Data Stores"
        PG[(PostgreSQL<br/>Source of Truth)]
        REDIS[(Redis<br/>Coordination Layer)]
        ETCD[(etcd<br/>Leader Election)]
    end

    subgraph "Worker Pool (auto-detected resources)"
        W1[Worker-1<br/>psutil auto-detect]
        W2[Worker-2<br/>psutil auto-detect]
        W3[Worker-3<br/>psutil auto-detect]
    end

    subgraph "Container Runtime"
        D1[Docker Engine<br/>Task Containers]
    end

    subgraph "Observability"
        PROM[Prometheus]
        GRAFANA[Grafana]
    end

    subgraph "Future: Kubernetes Native"
        OP[Kopf Operator]
        CRD_T[Task CRD]
        CRD_W[Worker CRD]
        HELM[Helm Chart]
    end

    CLI -->|REST| M1
    UI -->|REST + WebSocket + SSE| M1
    K8S_API --> OP
    OP --> M1

    M1 --> PG
    M1 --> REDIS
    M1 --> ETCD

    W1 --> REDIS
    W2 --> REDIS
    W3 --> REDIS

    W1 -.->|heartbeat + resource metrics| REDIS
    W2 -.->|heartbeat + resource metrics| REDIS
    W3 -.->|heartbeat + resource metrics| REDIS

    W1 -->|Docker SDK| D1
    W2 -->|Docker SDK| D1
    W3 -->|Docker SDK| D1

    M1 --> PROM
    PROM --> GRAFANA
```

## Task Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Task submitted (image + command specified)
    PENDING --> SCHEDULED: Worker assigned (spread scheduling)
    PENDING --> CANCELLED: User cancels

    SCHEDULED --> RUNNING: Worker pulls image, starts container
    SCHEDULED --> PENDING: Reschedule (worker failed)
    SCHEDULED --> CANCELLED: User cancels

    RUNNING --> COMPLETED: Container exits with code 0
    RUNNING --> FAILED: Container exits non-zero / OOM / timeout
    RUNNING --> PREEMPTED: Higher priority eviction (container stopped)
    RUNNING --> CANCELLED: User cancels (container stopped)

    FAILED --> PENDING: Retry (count < max)
    PREEMPTED --> PENDING: Re-enqueue

    COMPLETED --> [*]
    FAILED --> [*]: Retries exhausted
    CANCELLED --> [*]
```

## Scheduling Flow

```mermaid
sequenceDiagram
    participant C as Client / Dashboard
    participant M as Master API
    participant EB as EventBus
    participant PG as PostgreSQL
    participant RQ as Redis Queue
    participant SL as Scheduler Loop
    participant W as Worker
    participant D as Docker Engine

    C->>M: POST /api/v1/tasks (image, command, resources)
    M->>PG: INSERT task (state=PENDING, image, command, env_vars)
    M->>RQ: ZADD task_queue (score=-priority)
    M->>EB: publish(task_created)
    EB-->>C: WebSocket push
    M-->>C: 201 Created

    Note over SL,RQ: On startup: reconcile PENDING tasks from PG into Redis queue

    loop Every 1s (leader only)
        SL->>RQ: ZPOPMIN (dequeue highest priority)
        SL->>PG: SELECT active workers + resources
        SL->>SL: Spread scheduling (pick worker with most headroom)
        alt Worker found
            SL->>PG: UPDATE task state=SCHEDULED, assigned_worker
            SL->>RQ: RPUSH worker:{id}:assignments
            SL->>EB: publish(task_scheduled)
        else No capacity
            SL->>SL: Preemption engine
            alt Preemption succeeds
                SL->>RQ: Signal victim worker to stop container
                SL->>PG: Victim -> PREEMPTED, new -> SCHEDULED
            else Preemption fails
                SL->>RQ: Re-enqueue task
            end
        end
    end

    Note over SL,PG: Every ~60s: reconcile PENDING tasks missing from Redis

    W->>RQ: BLPOP worker:{id}:assignments
    W->>M: GET /api/v1/tasks/{id}
    W->>M: POST state=RUNNING
    W->>EB: publish(task_state_changed)
    W->>D: docker pull image
    W->>D: docker create (cpu_quota, mem_limit, env_vars)
    W->>D: docker start
    EB-->>C: WebSocket push (container_started)

    loop Every 500ms
        W->>D: container.status check
        W->>W: Check cancel_event + timeout
    end

    D-->>W: Container exits
    W->>D: container.logs (capture stdout/stderr)
    W->>D: container.remove
    W->>M: POST /internal/tasks/{id}/complete (exit_code, stdout, stderr, container_id)
    M->>EB: publish(container_exited)
    EB-->>C: WebSocket push
```

## Docker Container Execution Flow

```mermaid
flowchart TD
    A[Worker receives task assignment] --> B[Parse task data: image, command, env_vars, limits]
    B --> C[docker.images.pull - image:tag]
    C -->|Pull fails| ERR1[TaskExecutionError: image pull failed]
    C -->|Pull succeeds| D[docker.containers.create]

    D --> E[Set resource limits]
    E --> E1[cpu_quota = cpu_cores * 100000]
    E --> E2[mem_limit = memory_mb * 1048576]
    E --> E3[labels: chronos-task-id, chronos-worker-id]

    E1 --> F[container.start]
    E2 --> F
    E3 --> F

    F --> G{Monitor loop every 500ms}
    G -->|cancel_event set| H[container.stop + TaskPreemptedError]
    G -->|timeout exceeded| I[container.stop + TaskExecutionError: timeout]
    G -->|container running| G
    G -->|container exited| J{Inspect exit state}

    J -->|OOMKilled = true| K[TaskExecutionError: OOM killed]
    J -->|exit_code = 0| L[Capture logs, return success result]
    J -->|exit_code != 0| M[TaskExecutionError: exit code N]

    L --> N[container.remove force=True]
    H --> N
    I --> N
    K --> N
    M --> N
```

## Failure Detection Flow

```mermaid
sequenceDiagram
    participant W as Worker
    participant R as Redis
    participant FD as Failure Detector
    participant PG as PostgreSQL
    participant EB as EventBus

    loop Every 5s
        W->>W: psutil.cpu_percent(), psutil.virtual_memory()
        W->>W: Docker SDK container stats (aggregate)
        W->>R: SET worker:{id}:heartbeat (TTL=15s)<br/>payload: cpu_percent, memory_percent, container_count
    end

    Note over W: Worker crashes / network partition

    loop Every 10s (leader only)
        FD->>R: EXISTS worker:{id}:heartbeat
        alt Key exists
            FD->>FD: Worker alive, skip
        else Key expired (TTL)
            FD->>PG: UPDATE worker status=DEAD
            FD->>PG: SELECT orphaned tasks (RUNNING/SCHEDULED on dead worker)
            FD->>PG: Tasks -> PENDING (if retries remain)
            FD->>R: ZADD task_queue (re-enqueue)
            FD->>EB: publish(worker_dead)
            FD->>EB: publish(task_state_changed) for each orphaned task
        end
    end
```

## Preemption Flow

```mermaid
flowchart TD
    A[High-priority task arrives] --> B{Any worker has capacity?}
    B -->|Yes| C[Spread schedule normally]
    B -->|No| D[Preemption Engine activated]
    D --> E[For each active worker]
    E --> F[Find lower-priority running containers]
    F --> G{Evicting victims frees enough resources?}
    G -->|Yes| H[Record worker + victims + waste score]
    G -->|No| E
    H --> I[Select plan with minimum waste]
    I --> J[Signal worker to stop victim containers]
    J --> K[Transition victims -> PREEMPTED]
    K --> L[Re-enqueue victims if retries remain]
    L --> M[Schedule high-priority task on freed worker]
```

## Real-Time Event Flow

```mermaid
flowchart LR
    subgraph "Event Sources"
        TS[Task Service]
        WS[Worker Service]
        SL[Scheduler Loop]
        FD[Failure Detector]
        WA[Worker API<br/>complete/fail]
    end

    subgraph "Event Infrastructure"
        EB[EventBus<br/>asyncio.Queue per subscriber]
        WSE[WebSocket Endpoint<br/>/ws/events]
        SSE[SSE Endpoint<br/>/api/v1/tasks/id/logs]
    end

    subgraph "Consumers"
        DASH[Dashboard<br/>React + TanStack Query]
    end

    TS -->|task_created| EB
    WS -->|worker_registered<br/>worker_heartbeat<br/>worker_dead| EB
    SL -->|task_scheduled| EB
    FD -->|worker_dead<br/>task_state_changed| EB
    WA -->|container_exited<br/>oom_killed<br/>timeout_killed| EB

    EB --> WSE
    WSE -->|JSON events| DASH

    SSE -->|live container logs| DASH

    DASH -->|invalidate queries| DASH
```

## Spread Scheduling Algorithm

```mermaid
flowchart TD
    A[Task arrives: needs X cpu, Y memory] --> B[Get all ACTIVE workers]
    B --> C[Filter: cpu_available >= X AND memory_available >= Y]
    C --> D{Any candidates?}
    D -->|No| E[Try preemption]
    D -->|Yes| F[Calculate headroom for each worker]
    F --> G[headroom = cpu_remaining + mem_remaining/1024]
    G --> H[Sort by headroom DESCENDING]
    H --> I[Select worker with MOST remaining resources]
    I --> J[Deduct resources from worker]
    J --> K[Next task picks a different worker<br/>since first worker now has less headroom]

    style I fill:#2d6a4f,color:#fff
    style K fill:#2d6a4f,color:#fff
```

> **Why spread over best-fit?** When workers run on the same host (common in dev/test with Docker Compose), best-fit always picks the same worker because all workers report identical resources. Spread scheduling naturally round-robins tasks across all available nodes by always choosing the worker with the most remaining capacity.

## Worker Resource Reporting

```mermaid
flowchart TD
    subgraph "Scheduler-Tracked (Reservations)"
        ST1[cpu_available = total - reserved]
        ST2[memory_available = total - reserved]
    end

    subgraph "psutil (Actual OS Metrics)"
        PS1[cpu_percent = psutil.cpu_percent]
        PS2[memory_percent = psutil.virtual_memory.percent]
        PS3[actual_cpu_used = cpu_count * cpu_percent/100]
        PS4[actual_memory_used = used bytes -> MB]
    end

    subgraph "Docker Stats (Container Metrics)"
        DS1[container_count = len running containers]
        DS2[container_cpu_usage = sum container CPU%]
        DS3[container_memory_usage = sum container RSS MB]
    end

    ST1 --> HB[Heartbeat Payload]
    ST2 --> HB
    PS1 --> HB
    PS2 --> HB
    PS3 --> HB
    PS4 --> HB
    DS1 --> HB
    DS2 --> HB
    DS3 --> HB

    HB -->|Every 5s| REDIS[(Redis TTL key)]
    HB -->|via EventBus| DASH[Dashboard<br/>dual-bar resource gauges]
```

## Redis Data Layout

| Key Pattern | Type | Purpose |
|---|---|---|
| `chronos:task_queue` | Sorted Set | Priority queue (score = -priority) |
| `chronos:worker:{id}:heartbeat` | String + TTL | Heartbeat with 15s expiry (includes resource metrics) |
| `chronos:worker:{id}:assignments` | List | Per-worker task assignment queue |
| `chronos:worker:{id}:preempt` | List | Preemption signal queue |
| `chronos:worker:{id}:active_tasks` | Set | Currently running task IDs |
| `chronos:lock:scheduler` | Lock | Exclusive scheduler tick |
| `chronos:lock:preemption` | Lock | Exclusive preemption operation |

## Docker Container Labels

Each task container is labeled for identification and orphan cleanup:

| Label | Value | Purpose |
|---|---|---|
| `chronos.managed` | `true` | Identifies Chronos-managed containers |
| `chronos.task_id` | UUID | Links container to task |
| `chronos.worker_id` | string | Links container to worker |

On startup, workers query `chronos.managed=true` + `chronos.worker_id={self}` to find and remove orphaned containers from previous runs.
