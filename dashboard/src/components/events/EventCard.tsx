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
  Box,
  LogOut,
  Download,
  AlertTriangle,
  Timer,
} from "lucide-react";
import { formatRelativeTime } from "@/utils/format";
import type { WebSocketEvent, EventType } from "@/types/events";

const eventConfig: Record<
  string,
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
  container_started: {
    icon: Box,
    color: "text-cyan-400",
    label: "Container Started",
  },
  container_exited: {
    icon: LogOut,
    color: "text-gray-400",
    label: "Container Exited",
  },
  image_pull_started: {
    icon: Download,
    color: "text-yellow-400",
    label: "Image Pull",
  },
  image_pull_completed: {
    icon: Download,
    color: "text-emerald-400",
    label: "Image Ready",
  },
  oom_killed: {
    icon: AlertTriangle,
    color: "text-yellow-500",
    label: "OOM Killed",
  },
  timeout_killed: {
    icon: Timer,
    color: "text-red-500",
    label: "Timeout Killed",
  },
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
    if (
      (event.type === "task_state_changed" ||
        event.type === "oom_killed" ||
        event.type === "timeout_killed") &&
      "to_state" in d
    ) {
      const detail = `${d.name}: ${("from_state" in d ? d.from_state : "?")} → ${d.to_state}`;
      if ("image" in d && d.image) return `${detail} [${d.image}]`;
      return detail;
    }
    if (event.type === "task_scheduled" && "worker_hostname" in d) {
      return `${d.name} → ${d.worker_hostname}`;
    }
    if (event.type === "container_exited" && "exit_code" in d) {
      const exitStr = `exit ${d.exit_code}`;
      if ("image" in d) return `${d.name} (${d.image}) — ${exitStr}`;
      return `${d.name} — ${exitStr}`;
    }
    if ("image" in d && d.image) {
      return `${d.name} [${d.image}]`;
    }
    return `${d.name} (P${"priority" in d ? d.priority : "?"})`;
  }
  if ("hostname" in d) {
    return String(d.hostname);
  }
  return "";
}
