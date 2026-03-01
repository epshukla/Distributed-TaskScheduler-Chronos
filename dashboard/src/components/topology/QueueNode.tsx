import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Layers } from "lucide-react";

interface QueueNodeData {
  label: string;
  depth: number;
  maxDepth: number;
  [key: string]: unknown;
}

export const QueueNode = memo(function QueueNode({
  data,
}: NodeProps & { data: QueueNodeData }) {
  const fillPercent =
    data.maxDepth > 0
      ? Math.min((data.depth / data.maxDepth) * 100, 100)
      : 0;

  return (
    <div className="rounded-xl border-2 border-indigo-500/30 bg-surface-50 px-4 py-3">
      <Handle type="target" position={Position.Top} className="!bg-accent" />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-accent"
      />
      <div className="flex items-center gap-2">
        <Layers size={14} className="text-indigo-400" />
        <span className="text-sm font-medium text-gray-200">{data.label}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-100/30">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all duration-500"
          style={{ width: `${fillPercent}%` }}
        />
      </div>
      <p className="mt-1 text-[10px] text-gray-500">
        {data.depth} tasks queued
      </p>
    </div>
  );
});
