import { type LucideIcon } from "lucide-react";
import { AnimatedNumber } from "./AnimatedNumber";

interface KPICardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  iconColor?: string;
  precision?: number;
  suffix?: string;
  trend?: { value: number; label: string };
  sparklineData?: number[];
}

export function KPICard({
  title,
  value,
  icon: Icon,
  iconColor = "text-accent-light",
  precision = 0,
  suffix,
  sparklineData,
}: KPICardProps) {
  return (
    <div className="card-hover flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {title}
        </span>
        <Icon size={16} className={iconColor} />
      </div>
      <div className="flex items-end justify-between">
        <div className="flex items-baseline gap-1">
          <AnimatedNumber
            value={value}
            precision={precision}
            className="text-3xl font-bold text-gray-100"
          />
          {suffix && (
            <span className="text-sm text-gray-500">{suffix}</span>
          )}
        </div>
        {sparklineData && sparklineData.length > 1 && (
          <MiniSparkline data={sparklineData} />
        )}
      </div>
    </div>
  );
}

function MiniSparkline({ data }: { data: number[] }) {
  const max = Math.max(...data, 1);
  const h = 24;
  const w = 60;
  const step = w / (data.length - 1);
  const points = data
    .map((v, i) => `${i * step},${h - (v / max) * h}`)
    .join(" ");

  return (
    <svg width={w} height={h} className="text-accent">
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}
