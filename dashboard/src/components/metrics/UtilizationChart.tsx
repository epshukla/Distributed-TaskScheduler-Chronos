import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#3b82f6"];

interface UtilizationChartProps {
  workerUtilization: Map<string, { timestamp: number; value: number; label?: string }[]>;
}

export function UtilizationChart({ workerUtilization }: UtilizationChartProps) {
  const entries = Array.from(workerUtilization.entries());
  if (entries.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-600">
        Waiting for worker data...
      </div>
    );
  }

  // Merge all workers into time-aligned data points
  const maxLen = Math.max(...entries.map(([, points]) => points.length));
  const data = Array.from({ length: maxLen }).map((_, i) => {
    const row: Record<string, number | string> = { index: i };
    entries.forEach(([id, points], wIdx) => {
      const hostname = points[0]?.label || id.slice(0, 8);
      const pt = points[i];
      row[hostname] = pt ? Math.round(pt.value) : 0;
    });
    return row;
  });

  const hostnames = entries.map(
    ([id, points]) => points[0]?.label || id.slice(0, 8),
  );

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data}>
        <XAxis dataKey="index" hide />
        <YAxis
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
          domain={[0, 100]}
          unit="%"
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: "11px", color: "#94a3b8" }}
        />
        {hostnames.map((hostname, i) => (
          <Line
            key={hostname}
            type="monotone"
            dataKey={hostname}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={1.5}
            dot={false}
            animationDuration={300}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
