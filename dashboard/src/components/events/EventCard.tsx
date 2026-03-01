import { motion } from "framer-motion";
import {
  Plus,
  Calendar,
  Play,
  CheckCircle,
  XCircle,
  Server,
  Heart,
  Skull,
} from "lucide-react";
import { formatRelativeTime } from "@/utils/format";
import type { WebSocketEvent, EventType } from "@/types/events";

const eventConfig: Record<
  EventType,
  { icon: typeof Plus; color: string; label: string }
> = {
  task_created: { icon: Plus, color: "text-blue-400", label: "Task Created" },
  task_scheduled: {
    icon: Calendar,
    color: "text-indigo-400",
    label: "Task Scheduled",
  },
  task_state_changed: {
    icon: Play,
    color: "text-purple-400",
    label: "State Changed",
  },
  worker_registered: {
    icon: Server,
    color: "text-emerald-400",
    label: "Worker Registered",
  },
  worker_heartbeat: {
    icon: Heart,
    color: "text-gray-500",
    label: "Heartbeat",
  },
  worker_dead: { icon: Skull, color: "text-red-400", label: "Worker Dead" },
};

interface EventCardProps {
  event: WebSocketEvent;
}

export function EventCard({ event }: EventCardProps) {
  const config = eventConfig[event.type] || {
    icon: Plus,
    color: "text-gray-400",
    label: event.type,
  };
  const Icon = config.icon;

  const detail = getEventDetail(event);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-3 rounded-lg border border-surface-100/10 bg-surface-50/30 px-3 py-2"
    >
      <Icon size={14} className={`mt-0.5 shrink-0 ${config.color}`} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-medium text-gray-300">
            {config.label}
          </span>
          <span className="shrink-0 text-[10px] text-gray-600">
            {formatRelativeTime(event.timestamp)}
          </span>
        </div>
        {detail && (
          <p className="mt-0.5 truncate text-[11px] text-gray-500">{detail}</p>
        )}
      </div>
    </motion.div>
  );
}

function getEventDetail(event: WebSocketEvent): string {
  const d = event.data;
  if ("name" in d && "task_id" in d) {
    if (event.type === "task_state_changed" && "to_state" in d) {
      return `${d.name}: ${("from_state" in d ? d.from_state : "?")} → ${d.to_state}`;
    }
    if (event.type === "task_scheduled" && "worker_hostname" in d) {
      return `${d.name} → ${d.worker_hostname}`;
    }
    return `${d.name} (P${"priority" in d ? d.priority : "?"})`;
  }
  if ("hostname" in d) {
    return String(d.hostname);
  }
  return "";
}
