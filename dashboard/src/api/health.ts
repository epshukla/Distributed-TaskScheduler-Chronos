import { apiFetch } from "./client";
import type { HealthResponse, ReadinessResponse } from "@/types/health";

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  return apiFetch<ReadinessResponse>("/ready");
}
