import { apiFetch } from "./client";

export interface ClusterStats {
  queue_depth: number;
  state_counts: Record<string, number>;
  worker_task_counts: Record<string, number>;
  pipeline_active: number;
}

export async function fetchStats(): Promise<ClusterStats> {
  return apiFetch<ClusterStats>("/api/v1/stats");
}
