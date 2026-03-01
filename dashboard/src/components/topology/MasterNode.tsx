import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Crown } from "lucide-react";

interface MasterNodeData {
  label: string;
  isLeader: boolean;
  version: string;
  [key: string]: unknown;
}

export const MasterNode = memo(function MasterNode({
  data,
}: NodeProps & { data: MasterNodeData }) {
  return (
    <div
      className={`rounded-xl border-2 bg-surface-50 px-4 py-3 ${
        data.isLeader
          ? "animate-glow border-yellow-500/50"
          : "border-surface-100/30"
      }`}
    >
      <Handle type="source" position={Position.Bottom} className="!bg-accent" />
      <div className="flex items-center gap-2">
        {data.isLeader && <Crown size={14} className="text-yellow-400" />}
        <span className="text-sm font-bold text-gray-200">{data.label}</span>
      </div>
      <p className="mt-1 text-[10px] text-gray-500">
        {data.isLeader ? "Leader" : "Follower"} &middot; {data.version}
      </p>
    </div>
  );
});
