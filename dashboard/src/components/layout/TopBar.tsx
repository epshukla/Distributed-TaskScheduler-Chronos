import { Crown, Heart, Clock, Server } from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import { formatDuration } from "@/utils/format";

export function TopBar() {
  const { data: health } = useHealth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-surface-100/20 px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-sm font-medium text-gray-300">
          Distributed Task Scheduler
        </h1>
      </div>
      <div className="flex items-center gap-6">
        {health?.is_leader && (
          <div className="flex items-center gap-1.5 text-xs text-yellow-400">
            <Crown size={13} />
            <span>Leader</span>
          </div>
        )}
        {health && (
          <>
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <Server size={13} className="text-blue-400" />
              <span>{health.node_id}</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <Heart size={13} className="text-emerald-400" />
              <span>{health.status}</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <Clock size={13} />
              <span>Up {formatDuration(health.uptime_seconds)}</span>
            </div>
          </>
        )}
      </div>
    </header>
  );
}
