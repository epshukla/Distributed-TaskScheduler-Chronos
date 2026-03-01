# Chronos-K8s-Scheduler Architecture

## System Architecture

```mermaid
graph TB
    subgraph "Clients"
        CLI[CLI / curl]
        UI[Dashboard]
        K8S_API[kubectl + CRDs]
    end

    subgraph "Control Plane"
        subgraph "Master HA (2+ replicas)"
            M1[Master-1<br/>FastAPI + Scheduler]
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

    subgraph "Worker Pool (heterogeneous)"
        W1[Worker-1<br/>4 CPU / 4GB]
        W2[Worker-2<br/>4 CPU / 4GB]
        W3[Worker-3<br/>2 CPU / 2GB]
        W4[Worker-4<br/>2 CPU / 2GB]
        W5[Worker-5<br/>8 CPU / 8GB]
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

    CLI --> M1
    UI --> M1
    K8S_API --> OP
    OP --> M1

    M1 --> PG
    M1 --> REDIS
    M1 --> ETCD

    W1 --> REDIS
    W2 --> REDIS
    W3 --> REDIS
    W4 --> REDIS
    W5 --> REDIS

    W1 -.->|heartbeat| REDIS
    W2 -.->|heartbeat| REDIS
    W3 -.->|heartbeat| REDIS
    W4 -.->|heartbeat| REDIS
    W5 -.->|heartbeat| REDIS

    M1 --> PROM
    PROM --> GRAFANA
```

## Task Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Task submitted
    PENDING --> SCHEDULED: Worker assigned (bin-packing)
    PENDING --> CANCELLED: User cancels

    SCHEDULED --> RUNNING: Worker starts execution
    SCHEDULED --> PENDING: Reschedule (worker failed)
    SCHEDULED --> CANCELLED: User cancels

    RUNNING --> COMPLETED: Execution success
    RUNNING --> FAILED: Execution error
    RUNNING --> PREEMPTED: Higher priority eviction
    RUNNING --> CANCELLED: User cancels

    FAILED --> PENDING: Retry (count < max)
    PREEMPTED --> PENDING: Re-enqueue

    COMPLETED --> [*]
    FAILED --> [*]: Retries exhausted
    CANCELLED --> [*]
```

## Scheduling Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant M as Master API
    participant PG as PostgreSQL
    participant RQ as Redis Queue
    participant SL as Scheduler Loop
    participant W as Worker

    C->>M: POST /api/v1/tasks
    M->>PG: INSERT task (state=PENDING)
    M->>RQ: ZADD task_queue (score=-priority)
    M-->>C: 201 Created

    Note over SL,RQ: On startup: reconcile PENDING tasks from PG into Redis queue

    loop Every 1s (leader only)
        SL->>RQ: ZPOPMIN (dequeue highest priority)
        SL->>PG: SELECT active workers + resources
        SL->>SL: Best-fit bin-packing algorithm
        alt Worker found
            SL->>PG: UPDATE task state=SCHEDULED
            SL->>RQ: RPUSH worker:{id}:assignments
        else No capacity
            SL->>SL: Preemption engine
            alt Preemption succeeds
                SL->>RQ: Signal victim worker
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
    W->>W: Execute task (simulate workload)
    W->>M: POST /internal/tasks/{id}/complete
```

## Failure Detection Flow

```mermaid
sequenceDiagram
    participant W as Worker
    participant R as Redis
    participant FD as Failure Detector
    participant PG as PostgreSQL

    loop Every 5s
        W->>R: SET worker:{id}:heartbeat (TTL=15s)
    end

    Note over W: Worker crashes / network partition

    loop Every 10s (leader only)
        FD->>R: EXISTS worker:{id}:heartbeat
        alt Key exists
            FD->>FD: Worker alive, skip
        else Key expired (TTL)
            FD->>PG: UPDATE worker status=DEAD
            FD->>PG: SELECT orphaned tasks
            FD->>PG: Tasks -> PENDING (if retries remain)
            FD->>R: ZADD task_queue (re-enqueue)
        end
    end
```

## Preemption Flow

```mermaid
flowchart TD
    A[High-priority task arrives] --> B{Any worker has capacity?}
    B -->|Yes| C[Best-fit schedule normally]
    B -->|No| D[Preemption Engine activated]
    D --> E[For each active worker]
    E --> F[Find lower-priority running tasks]
    F --> G{Evicting victims frees enough resources?}
    G -->|Yes| H[Record worker + victims + waste score]
    G -->|No| E
    H --> I[Select plan with minimum waste]
    I --> J[Signal worker to stop victims]
    J --> K[Transition victims -> PREEMPTED]
    K --> L[Re-enqueue victims if retries remain]
    L --> M[Schedule high-priority task on freed worker]
```

## Redis Data Layout

| Key Pattern | Type | Purpose |
|---|---|---|
| `chronos:task_queue` | Sorted Set | Priority queue (score = -priority) |
| `chronos:worker:{id}:heartbeat` | String + TTL | Heartbeat with 15s expiry |
| `chronos:worker:{id}:assignments` | List | Per-worker task assignment queue |
| `chronos:worker:{id}:preempt` | List | Preemption signal queue |
| `chronos:worker:{id}:active_tasks` | Set | Currently running task IDs |
| `chronos:lock:scheduler` | Lock | Exclusive scheduler tick |
| `chronos:lock:preemption` | Lock | Exclusive preemption operation |
