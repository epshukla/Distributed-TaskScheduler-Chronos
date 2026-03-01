export enum WorkerStatus {
  ACTIVE = "ACTIVE",
  DEAD = "DEAD",
  DRAINING = "DRAINING",
}

export interface Worker {
  id: string;
  hostname: string;
  status: WorkerStatus;
  cpu_total: number;
  cpu_available: number;
  memory_total: number;
  memory_available: number;
  last_heartbeat: string;
  registered_at: string;
}

export interface WorkerRegister {
  hostname: string;
  cpu_total: number;
  memory_total: number;
}
