import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Server } from "lucide-react";
import { CircularGauge } from "@/components/common/CircularGauge";

interface WorkerNodeData {
  hostname: string;
  status: string;
  cpuUsed: number;
  cpuTotal: number;
  memUsed: number;
  memTotal: number;
  taskCount: number;
  [key: string]: unknown;
}

export const WorkerNode = memo(function WorkerNode({
  data,
}: NodeProps & { data: WorkerNodeData }) {
  const isAlive = data.status === "ACTIVE";
  const borderColor = isAlive ? "border-emerald-500/40" : "border-red-500/40";

  return (
    <div className={`rounded-xl border-2 bg-surface-50 px-4 py-3 ${borderColor}`}>
      <Handle type="target" position={Position.Top} className="!bg-accent" />
      <div className="flex items-center gap-2">
        <Server
          size={14}
          className={isAlive ? "text-emerald-400" : "text-red-400"}
        />
        <span className="text-xs font-medium text-gray-200">
          {data.hostname}
        </span>
      </div>
      <div className="mt-2 flex items-center justify-center gap-3">
        <CircularGauge
          value={data.cpuUsed}
          max={data.cpuTotal}
          size={48}
          strokeWidth={4}
          label="CPU"
        />
        <CircularGauge
          value={data.memUsed}
          max={data.memTotal}
          size={48}
          strokeWidth={4}
          label="MEM"
        />
      </div>
      <p className="mt-1 text-center text-[10px] text-gray-500">
        {data.taskCount} task{data.taskCount !== 1 ? "s" : ""}
      </p>
    </div>
  );
});
