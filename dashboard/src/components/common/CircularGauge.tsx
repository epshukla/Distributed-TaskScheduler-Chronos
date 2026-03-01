import { utilizationColor } from "@/utils/colors";

interface CircularGaugeProps {
  value: number;
  max: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function CircularGauge({
  value,
  max,
  size = 64,
  strokeWidth = 5,
  label,
}: CircularGaugeProps) {
  const percent = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  const color = utilizationColor(percent);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#334155"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xs font-bold text-gray-200">
          {Math.round(percent)}%
        </span>
        {label && (
          <span className="text-[9px] text-gray-500">{label}</span>
        )}
      </div>
    </div>
  );
}
