import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PriorityBadge } from "@/components/common/PriorityBadge";
import { RelativeTime } from "@/components/common/RelativeTime";
import { TaskStateTimeline } from "./TaskStateTimeline";
import { useCancelTask } from "@/hooks/useTasks";
import { TaskState } from "@/types/task";
import type { Task } from "@/types/task";

interface TaskDetailDrawerProps {
  task: Task;
  onClose: () => void;
}

export function TaskDetailDrawer({ task, onClose }: TaskDetailDrawerProps) {
  const cancelTask = useCancelTask();
  const canCancel = ![TaskState.COMPLETED, TaskState.CANCELLED, TaskState.FAILED].includes(
    task.state as TaskState,
  );

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/50"
        onClick={onClose}
      />
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 z-50 h-full w-[480px] overflow-auto border-l border-surface-100/20 bg-surface p-6"
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-100">{task.name}</h3>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-surface-50"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mt-6 space-y-6">
          <div className="flex items-center gap-3">
            <StatusBadge state={task.state} size="md" />
            <PriorityBadge priority={task.priority} />
          </div>

          <TaskStateTimeline task={task} />

          <div className="space-y-3">
            <DetailRow label="ID" value={task.id} mono />
            {task.description && (
              <DetailRow label="Description" value={task.description} />
            )}
            <DetailRow
              label="Resources"
              value={`${task.resource_cpu} CPU / ${task.resource_memory} MB`}
            />
            <DetailRow
              label="Duration"
              value={`${task.duration_seconds}s`}
            />
            <DetailRow
              label="Retries"
              value={`${task.retry_count} / ${task.max_retries}`}
            />
            {task.assigned_worker_id && (
              <DetailRow
                label="Worker"
                value={task.assigned_worker_id.slice(0, 8)}
                mono
              />
            )}
            <DetailRow
              label="Created"
              value={<RelativeTime date={task.created_at} />}
            />
            {task.error && (
              <DetailRow
                label="Error"
                value={
                  <span className="text-red-400">{task.error}</span>
                }
              />
            )}
          </div>

          {canCancel && (
            <button
              onClick={() => cancelTask.mutate(task.id)}
              disabled={cancelTask.isPending}
              className="w-full rounded-lg border border-red-500/30 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/10 disabled:opacity-50"
            >
              {cancelTask.isPending ? "Cancelling..." : "Cancel Task"}
            </button>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-xs text-gray-500">{label}</span>
      <span
        className={`text-sm text-gray-300 ${mono ? "font-mono text-xs" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
