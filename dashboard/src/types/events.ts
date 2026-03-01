export type EventType =
  | "task_created"
  | "task_scheduled"
  | "task_state_changed"
  | "worker_registered"
  | "worker_heartbeat"
  | "worker_dead"
  | "container_started"
  | "container_exited"
  | "image_pull_started"
  | "image_pull_completed"
  | "oom_killed"
  | "timeout_killed";

export interface TaskCreatedPayload {
  task_id: string;
  name: string;
  priority: number;
  state: string;
  resource_cpu: number;
  resource_memory: number;
  image?: string;
}

export interface TaskScheduledPayload {
  task_id: string;
  name: string;
  worker_id: string;
  worker_hostname: string;
  priority: number;
  resource_cpu: number;
  resource_memory: number;
}

export interface TaskStateChangedPayload {
  task_id: string;
  name: string;
  from_state: string;
  to_state: string;
  worker_id?: string | null;
  reason?: string;
  retry_count?: number;
  exit_code?: number | null;
  image?: string;
  error?: string;
}

export interface ContainerExitedPayload {
  task_id: string;
  name: string;
  image: string;
  exit_code: number;
  container_id: string;
}

export interface WorkerRegisteredPayload {
  worker_id: string;
  hostname: string;
  cpu_total: number;
  memory_total: number;
  status: string;
}

export interface WorkerHeartbeatPayload {
  worker_id: string;
  hostname: string;
  cpu_available: number;
  memory_available: number;
  cpu_total: number;
  memory_total: number;
}

export interface WorkerDeadPayload {
  worker_id: string;
  hostname: string;
}

export type EventPayload =
  | TaskCreatedPayload
  | TaskScheduledPayload
  | TaskStateChangedPayload
  | ContainerExitedPayload
  | WorkerRegisteredPayload
  | WorkerHeartbeatPayload
  | WorkerDeadPayload;

export interface WebSocketEvent {
  type: EventType;
  data: EventPayload;
  timestamp: string;
}
