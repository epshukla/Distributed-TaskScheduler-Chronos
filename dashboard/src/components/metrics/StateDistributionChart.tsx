import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { taskStateHex } from "@/utils/colors";
import { TaskState } from "@/types/task";
import type { Task } from "@/types/task";

interface StateDistributionChartProps {
  tasks: Task[];
}

export function StateDistributionChart({
  tasks,
}: StateDistributionChartProps) {
  const counts = Object.values(TaskState).map((state) => ({
    name: state,
    value: tasks.filter((t) => t.state === state).length,
    color: taskStateHex[state],
  }));

  const nonZero = counts.filter((c) => c.value > 0);

  if (nonZero.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-600">
        No tasks yet
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <ResponsiveContainer width={160} height={160}>
        <PieChart>
          <Pie
            data={nonZero}
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={70}
            paddingAngle={2}
            dataKey="value"
            animationDuration={500}
          >
            {nonZero.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
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
      <div className="flex flex-col gap-1.5">
        {nonZero.map((entry) => (
          <div key={entry.name} className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-xs text-gray-400">{entry.name}</span>
            <span className="text-xs font-medium text-gray-200">
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
