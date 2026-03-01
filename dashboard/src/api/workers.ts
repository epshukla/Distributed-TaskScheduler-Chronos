import { apiFetch } from "./client";
import type { Worker } from "@/types/worker";

export async function fetchWorkers(status?: string): Promise<Worker[]> {
  const qs = status ? `?status=${status}` : "";
  return apiFetch<Worker[]>(`/api/v1/workers${qs}`);
}

export async function fetchWorker(workerId: string): Promise<Worker> {
  return apiFetch<Worker>(`/api/v1/workers/${workerId}`);
}
