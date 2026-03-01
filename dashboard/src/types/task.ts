export enum TaskState {
  PENDING = "PENDING",
  SCHEDULED = "SCHEDULED",
  RUNNING = "RUNNING",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
}

export interface Task {
  id: string;
  name: string;
  description: string | null;
  priority: number;
  state: TaskState;
  resource_cpu: number;
  resource_memory: number;
  max_retries: number;
  retry_count: number;
  assigned_worker_id: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;

  // Docker container execution
  image: string;
  command: string[] | null;
  args: string[] | null;
  env_vars: Record<string, string> | null;
  working_dir: string | null;
  timeout_seconds: number;
  exit_code: number | null;
  stdout: string | null;
  stderr: string | null;
  container_id: string | null;
}

export interface TaskCreate {
  name: string;
  description?: string;
  priority?: number;
  resource_cpu?: number;
  resource_memory?: number;
  max_retries?: number;

  // Docker container execution
  image: string;
  command?: string[];
  args?: string[];
  env_vars?: Record<string, string>;
  working_dir?: string;
  timeout_seconds?: number;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TaskTemplate {
  name: string;
  image: string;
  command?: string[];
  resource_cpu: number;
  resource_memory: number;
  timeout_seconds?: number;
  description: string;
}
