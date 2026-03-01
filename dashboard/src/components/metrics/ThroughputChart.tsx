import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface ThroughputChartProps {
  data: { timestamp: number; value: number }[];
}

export function ThroughputChart({ data }: ThroughputChartProps) {
  const formatted = data.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString([], {
      minute: "2-digit",
      second: "2-digit",
    }),
    tasks: d.value,
  }));

  if (formatted.length < 2) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-600">
        Collecting data...
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={formatted}>
        <defs>
          <linearGradient id="throughputGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="time"
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
        <Area
          type="monotone"
          dataKey="tasks"
          stroke="#6366f1"
          strokeWidth={2}
          fill="url(#throughputGradient)"
          animationDuration={300}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
