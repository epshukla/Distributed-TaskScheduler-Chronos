import { apiFetch } from "./client";
import type { Task, TaskCreate, TaskListResponse } from "@/types/task";

export async function fetchTasks(params?: {
  state?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}): Promise<TaskListResponse> {
  const query = new URLSearchParams();
  if (params?.state) query.set("state", params.state);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.sort_order) query.set("sort_order", params.sort_order);
  const qs = query.toString();
  return apiFetch<TaskListResponse>(`/api/v1/tasks${qs ? `?${qs}` : ""}`);
}

export async function fetchTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/api/v1/tasks/${taskId}`);
}

export async function createTask(data: TaskCreate): Promise<Task> {
  return apiFetch<Task>("/api/v1/tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function cancelTask(taskId: string): Promise<Task> {
  return apiFetch<Task>(`/api/v1/tasks/${taskId}`, {
    method: "DELETE",
  });
}
