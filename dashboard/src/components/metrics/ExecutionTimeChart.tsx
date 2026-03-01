import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Task } from "@/types/task";

interface ExecutionTimeChartProps {
  tasks: Task[];
}

const BUCKETS = [
  { label: "<5s", max: 5 },
  { label: "5-15s", max: 15 },
  { label: "15-30s", max: 30 },
  { label: "30-60s", max: 60 },
  { label: "1-5m", max: 300 },
  { label: ">5m", max: Infinity },
];

export function ExecutionTimeChart({ tasks }: ExecutionTimeChartProps) {
  const completedTasks = tasks.filter(
    (t) => t.started_at && t.completed_at,
  );

  const data = BUCKETS.map((bucket) => ({
    name: bucket.label,
    count: 0,
  }));

  completedTasks.forEach((t) => {
    const start = new Date(t.started_at!).getTime();
    const end = new Date(t.completed_at!).getTime();
    const durationSec = (end - start) / 1000;
    for (let i = 0; i < BUCKETS.length; i++) {
      if (durationSec <= BUCKETS[i].max) {
        data[i].count++;
        break;
      }
    }
  });

  if (completedTasks.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-600">
        No execution data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <XAxis
          dataKey="name"
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
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
        <Bar
          dataKey="count"
          fill="#06b6d4"
          radius={[4, 4, 0, 0]}
          animationDuration={500}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
