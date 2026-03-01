import { utilizationColor } from "@/utils/colors";

interface WorkerResourceGaugeProps {
  label: string;
  used: number;
  total: number;
  unit: string;
}

export function WorkerResourceGauge({
  label,
  used,
  total,
  unit,
}: WorkerResourceGaugeProps) {
  const clampedUsed = Math.max(0, used);
  const percent = total > 0 ? Math.max(0, Math.min(100, (clampedUsed / total) * 100)) : 0;
  const color = utilizationColor(percent);

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px]">
        <span className="text-gray-500">{label}</span>
        <span className="text-gray-400">
          {clampedUsed.toFixed(1)} / {total.toFixed(1)} {unit}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-100/30">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${Math.min(percent, 100)}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}
