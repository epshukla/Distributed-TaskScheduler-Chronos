import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Task } from "@/types/task";

interface LatencyHistogramProps {
  tasks: Task[];
}

const BUCKETS = [
  { label: "<100ms", max: 0.1 },
  { label: "100-500ms", max: 0.5 },
  { label: "0.5-1s", max: 1 },
  { label: "1-5s", max: 5 },
  { label: "5-10s", max: 10 },
  { label: ">10s", max: Infinity },
];

export function LatencyHistogram({ tasks }: LatencyHistogramProps) {
  const scheduledTasks = tasks.filter(
    (t) => t.created_at && t.scheduled_at,
  );

  const data = BUCKETS.map((bucket) => ({
    name: bucket.label,
    count: 0,
  }));

  scheduledTasks.forEach((t) => {
    const latency =
      (new Date(t.scheduled_at!).getTime() -
        new Date(t.created_at).getTime()) /
      1000;
    for (let i = 0; i < BUCKETS.length; i++) {
      if (latency <= BUCKETS[i].max) {
        data[i].count++;
        break;
      }
    }
  });

  if (scheduledTasks.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-600">
        No scheduling data yet
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
          fill="#6366f1"
          radius={[4, 4, 0, 0]}
          animationDuration={500}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
