import { useState } from "react";
import { useTasks } from "@/hooks/useTasks";
import { TaskRow } from "./TaskRow";
import { TaskDetailDrawer } from "./TaskDetailDrawer";
import { TableSkeleton } from "@/components/common/SkeletonLoader";
import { TaskState } from "@/types/task";
import type { Task } from "@/types/task";
import { ChevronLeft, ChevronRight } from "lucide-react";

const stateFilters = ["All", ...Object.values(TaskState)];

export function TaskTable() {
  const [stateFilter, setStateFilter] = useState<string>("All");
  const [page, setPage] = useState(1);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const { data, isLoading } = useTasks({
    state: stateFilter === "All" ? undefined : stateFilter,
    page,
    page_size: 20,
    sort_by: "created_at",
    sort_order: "desc",
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {stateFilters.map((s) => (
          <button
            key={s}
            onClick={() => {
              setStateFilter(s);
              setPage(1);
            }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              stateFilter === s
                ? "bg-accent text-white"
                : "bg-surface-50 text-gray-400 hover:text-gray-200"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-surface-100/20">
        <table className="w-full">
          <thead>
            <tr className="border-b border-surface-100/20 bg-surface-50/30">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                State
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                Priority
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                Resources
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">
                Created
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="p-4">
                  <TableSkeleton rows={5} />
                </td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className="py-12 text-center text-sm text-gray-600"
                >
                  No tasks found
                </td>
              </tr>
            ) : (
              data?.items.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  onClick={setSelectedTask}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && data.pages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Page {data.page} of {data.pages} ({data.total} total)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-lg p-2 text-gray-400 hover:bg-surface-50 disabled:opacity-30"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
              disabled={page >= data.pages}
              className="rounded-lg p-2 text-gray-400 hover:bg-surface-50 disabled:opacity-30"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {selectedTask && (
        <TaskDetailDrawer
          task={selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </div>
  );
}
