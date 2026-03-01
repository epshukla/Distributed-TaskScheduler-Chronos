import { taskStateColor, workerStatusDot } from "@/utils/colors";
import { TaskState } from "@/types/task";

interface StatusBadgeProps {
  state: string;
  size?: "sm" | "md";
}

export function StatusBadge({ state, size = "sm" }: StatusBadgeProps) {
  const colorClass = taskStateColor[state] || "bg-gray-600 text-white";
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  const isRunning = state === TaskState.RUNNING;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${colorClass} ${sizeClass}`}
    >
      {isRunning && (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white/60"></span>
          <span className="relative inline-flex h-2 w-2 rounded-full bg-white"></span>
        </span>
      )}
      {state}
    </span>
  );
}

interface WorkerStatusBadgeProps {
  status: string;
}

export function WorkerStatusBadge({ status }: WorkerStatusBadgeProps) {
  const dotColor = workerStatusDot[status] || "bg-gray-500";
  const textColor =
    status === "ACTIVE"
      ? "text-emerald-400"
      : status === "DEAD"
        ? "text-red-400"
        : "text-yellow-400";

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${textColor}`}>
      <span className={`h-2 w-2 rounded-full ${dotColor}`} />
      {status}
    </span>
  );
}
