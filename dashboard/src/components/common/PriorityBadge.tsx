import { priorityColor } from "@/utils/colors";

interface PriorityBadgeProps {
  priority: number;
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const color = priorityColor(priority);
  return (
    <span
      className={`inline-flex items-center rounded-md border border-current/20 px-1.5 py-0.5 text-xs font-mono font-medium ${color}`}
    >
      P{priority}
    </span>
  );
}
