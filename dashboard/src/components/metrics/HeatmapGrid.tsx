import { utilizationColor } from "@/utils/colors";
import type { Worker } from "@/types/worker";

interface HeatmapGridProps {
  workers: Worker[];
}

export function HeatmapGrid({ workers }: HeatmapGridProps) {
  if (workers.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-gray-600">
        No workers
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="grid gap-2" style={{ gridTemplateColumns: `80px repeat(2, 1fr)` }}>
        <div />
        <div className="text-center text-[10px] text-gray-500">CPU</div>
        <div className="text-center text-[10px] text-gray-500">Memory</div>
      </div>
      {workers.map((w) => {
        const cpuPercent =
          w.cpu_total > 0
            ? ((w.cpu_total - w.cpu_available) / w.cpu_total) * 100
            : 0;
        const memPercent =
          w.memory_total > 0
            ? ((w.memory_total - w.memory_available) / w.memory_total) * 100
            : 0;

        return (
          <div
            key={w.id}
            className="grid gap-2"
            style={{ gridTemplateColumns: `80px repeat(2, 1fr)` }}
          >
            <span className="truncate text-xs text-gray-400">
              {w.hostname}
            </span>
            <div
              className="flex h-8 items-center justify-center rounded text-[10px] font-medium text-white"
              style={{ backgroundColor: utilizationColor(cpuPercent) }}
            >
              {Math.round(cpuPercent)}%
            </div>
            <div
              className="flex h-8 items-center justify-center rounded text-[10px] font-medium text-white"
              style={{ backgroundColor: utilizationColor(memPercent) }}
            >
              {Math.round(memPercent)}%
            </div>
          </div>
        );
      })}
    </div>
  );
}
