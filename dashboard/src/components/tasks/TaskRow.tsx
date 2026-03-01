import { useEffect, useRef, useState } from "react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { RelativeTime } from "@/components/common/RelativeTime";
import { truncate } from "@/utils/format";
import type { Task } from "@/types/task";

interface TaskRowProps {
  task: Task;
  onClick: (task: Task) => void;
  flash?: boolean;
}

export function TaskRow({ task, onClick, flash }: TaskRowProps) {
  const [shouldFlash, setShouldFlash] = useState(false);
  const prevState = useRef(task.state);

  useEffect(() => {
    if (task.state !== prevState.current || flash) {
      setShouldFlash(true);
      prevState.current = task.state;
      const timer = setTimeout(() => setShouldFlash(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [task.state, task.updated_at, flash]);

  const exitCodeClass =
    task.exit_code === null
      ? "text-gray-600"
      : task.exit_code === 0
        ? "text-emerald-400"
        : "text-red-400";

  return (
    <tr
      onClick={() => onClick(task)}
      className={`cursor-pointer border-b border-surface-100/10 transition-colors hover:bg-surface-50/50 ${
        shouldFlash ? "animate-flash-row" : ""
      }`}
    >
      <td className="px-4 py-3 text-xs font-mono text-gray-500">
        {task.id.slice(0, 8)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-200">
        {truncate(task.name, 25)}
      </td>
      <td className="px-4 py-3">
        <StatusBadge state={task.state} />
      </td>
      <td className="px-4 py-3">
        <span className="rounded bg-surface-50/80 px-1.5 py-0.5 font-mono text-[10px] text-gray-400">
          {truncate(task.image, 20)}
        </span>
      </td>
      <td className="px-4 py-3">
        <PriorityBadge priority={task.priority} />
      </td>
      <td className={`px-4 py-3 text-xs font-mono ${exitCodeClass}`}>
        {task.exit_code !== null ? task.exit_code : "—"}
      </td>
      <td className="px-4 py-3 text-xs text-gray-400">
        {task.resource_cpu}c / {task.resource_memory}MB
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        <RelativeTime date={task.created_at} />
      </td>
    </tr>
  );
}
