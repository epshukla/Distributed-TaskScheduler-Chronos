import { utilizationColor } from "@/utils/colors";

interface WorkerResourceGaugeProps {
  label: string;
  used: number;
  total: number;
  unit: string;
  actualUsed?: number;
}

export function WorkerResourceGauge({
  label,
  used,
  total,
  unit,
  actualUsed,
}: WorkerResourceGaugeProps) {
  const clampedUsed = Math.max(0, used);
  const percent = total > 0 ? Math.max(0, Math.min(100, (clampedUsed / total) * 100)) : 0;
  const color = utilizationColor(percent);

  const hasActual = actualUsed !== undefined && actualUsed >= 0;
  const actualPercent = hasActual && total > 0
    ? Math.max(0, Math.min(100, (actualUsed / total) * 100))
    : 0;

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px]">
        <span className="text-gray-500">{label}</span>
        <span className="text-gray-400">
          {clampedUsed.toFixed(1)} / {total.toFixed(1)} {unit}
          {hasActual && (
            <span className="ml-1 text-gray-600">
              (real: {actualUsed.toFixed(1)})
            </span>
          )}
        </span>
      </div>
      <div className="relative h-2 overflow-hidden rounded-full bg-surface-100/30">
        {/* Requested (scheduler-tracked) bar */}
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500 opacity-40"
          style={{
            width: `${Math.min(percent, 100)}%`,
            backgroundColor: color,
          }}
        />
        {/* Actual (psutil-measured) bar overlaid */}
        {hasActual && (
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(actualPercent, 100)}%`,
              backgroundColor: utilizationColor(actualPercent),
            }}
          />
        )}
        {!hasActual && (
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(percent, 100)}%`,
              backgroundColor: color,
            }}
          />
        )}
      </div>
      {hasActual && (
        <div className="flex gap-3 text-[9px]">
          <span className="flex items-center gap-1">
            <span className="inline-block h-1.5 w-1.5 rounded-full opacity-40" style={{ backgroundColor: color }} />
            <span className="text-gray-600">Requested</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-1.5 w-1.5 rounded-full" style={{ backgroundColor: utilizationColor(actualPercent) }} />
            <span className="text-gray-600">Actual</span>
          </span>
        </div>
      )}
    </div>
  );
}
