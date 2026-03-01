import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { Task } from "@/types/task";

interface ExitCodeChartProps {
  tasks: Task[];
}

const COLORS: Record<string, string> = {
  "Exit 0": "#10b981",
  "Non-zero": "#ef4444",
  "No exit": "#64748b",
};

export function ExitCodeChart({ tasks }: ExitCodeChartProps) {
  const exitZero = tasks.filter((t) => t.exit_code === 0).length;
  const nonZero = tasks.filter((t) => t.exit_code !== null && t.exit_code !== 0).length;
  const noExit = tasks.filter((t) => t.exit_code === null).length;

  const data = [
    { name: "Exit 0", value: exitZero },
    { name: "Non-zero", value: nonZero },
    { name: "No exit", value: noExit },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-600">
        No exit code data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={70}
          dataKey="value"
          animationDuration={500}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={COLORS[entry.name] || "#64748b"}
            />
          ))}
        </Pie>
        <Legend
          formatter={(value) => (
            <span style={{ color: "#94a3b8", fontSize: 11 }}>{value}</span>
          )}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "8px",
            fontSize: "12px",
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
