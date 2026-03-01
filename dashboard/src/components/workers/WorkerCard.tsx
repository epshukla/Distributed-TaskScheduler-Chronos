import { motion } from "framer-motion";
import { Server, Box } from "lucide-react";
import { WorkerStatusBadge } from "@/components/common/StatusBadge";
import { RelativeTime } from "@/components/common/RelativeTime";
import { WorkerResourceGauge } from "./WorkerResourceGauge";
import { workerStatusColor } from "@/utils/colors";
import type { Worker } from "@/types/worker";

interface WorkerCardProps {
  worker: Worker;
}

export function WorkerCard({ worker }: WorkerCardProps) {
  const borderColor = workerStatusColor[worker.status] || "border-gray-700";
  const cpuUsed = Math.max(0, worker.cpu_total - worker.cpu_available);
  const memUsed = Math.max(0, worker.memory_total - worker.memory_available);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`card-hover border-l-2 ${borderColor}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Server
            size={14}
            className={
              worker.status === "ACTIVE" ? "text-emerald-400" : "text-red-400"
            }
          />
          <span className="text-sm font-medium text-gray-200">
            {worker.hostname}
          </span>
        </div>
        <WorkerStatusBadge status={worker.status} />
      </div>

      <div className="mt-4 space-y-2">
        <WorkerResourceGauge
          label="CPU"
          used={cpuUsed}
          total={worker.cpu_total}
          unit="cores"
        />
        <WorkerResourceGauge
          label="Memory"
          used={memUsed}
          total={worker.memory_total}
          unit="MB"
        />
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-surface-100/10 pt-2">
        <span className="text-[10px] text-gray-600">
          ID: {worker.id.slice(0, 8)}
        </span>
        <span className="text-[10px] text-gray-600">
          Heartbeat: <RelativeTime date={worker.last_heartbeat} />
        </span>
      </div>
    </motion.div>
  );
}
