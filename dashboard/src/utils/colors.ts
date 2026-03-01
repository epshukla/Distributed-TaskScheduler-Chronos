import { TaskState } from "@/types/task";
import { WorkerStatus } from "@/types/worker";

export const taskStateColor: Record<string, string> = {
  [TaskState.PENDING]: "bg-state-pending text-black",
  [TaskState.SCHEDULED]: "bg-state-scheduled text-white",
  [TaskState.RUNNING]: "bg-state-running text-white",
  [TaskState.COMPLETED]: "bg-state-completed text-white",
  [TaskState.FAILED]: "bg-state-failed text-white",
  [TaskState.CANCELLED]: "bg-state-cancelled text-white",
};

export const taskStateDot: Record<string, string> = {
  [TaskState.PENDING]: "bg-state-pending",
  [TaskState.SCHEDULED]: "bg-state-scheduled",
  [TaskState.RUNNING]: "bg-state-running",
  [TaskState.COMPLETED]: "bg-state-completed",
  [TaskState.FAILED]: "bg-state-failed",
  [TaskState.CANCELLED]: "bg-state-cancelled",
};

export const taskStateHex: Record<string, string> = {
  [TaskState.PENDING]: "#f59e0b",
  [TaskState.SCHEDULED]: "#3b82f6",
  [TaskState.RUNNING]: "#8b5cf6",
  [TaskState.COMPLETED]: "#10b981",
  [TaskState.FAILED]: "#ef4444",
  [TaskState.CANCELLED]: "#6b7280",
};

export const workerStatusColor: Record<string, string> = {
  [WorkerStatus.ACTIVE]: "border-worker-active",
  [WorkerStatus.DEAD]: "border-worker-dead",
  [WorkerStatus.DRAINING]: "border-worker-draining",
};

export const workerStatusDot: Record<string, string> = {
  [WorkerStatus.ACTIVE]: "bg-worker-active",
  [WorkerStatus.DEAD]: "bg-worker-dead",
  [WorkerStatus.DRAINING]: "bg-worker-draining",
};

export function priorityColor(priority: number): string {
  if (priority >= 8) return "text-red-400";
  if (priority >= 5) return "text-yellow-400";
  if (priority >= 3) return "text-blue-400";
  return "text-gray-400";
}

export function utilizationColor(percent: number): string {
  if (percent >= 90) return "#ef4444";
  if (percent >= 70) return "#f59e0b";
  if (percent >= 40) return "#3b82f6";
  return "#10b981";
}
