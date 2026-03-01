import { CheckCircle, Circle, Clock } from "lucide-react";
import { taskStateDot } from "@/utils/colors";
import { TaskState } from "@/types/task";
import type { Task } from "@/types/task";

const LIFECYCLE: TaskState[] = [
  TaskState.PENDING,
  TaskState.SCHEDULED,
  TaskState.RUNNING,
  TaskState.COMPLETED,
];

export function TaskStateTimeline({ task }: { task: Task }) {
  const currentIndex = LIFECYCLE.indexOf(task.state as TaskState);
  const isFailed = task.state === TaskState.FAILED;
  const isCancelled = task.state === TaskState.CANCELLED;

  const timestamps: Record<string, string | null> = {
    [TaskState.PENDING]: task.created_at,
    [TaskState.SCHEDULED]: task.scheduled_at,
    [TaskState.RUNNING]: task.started_at,
    [TaskState.COMPLETED]: task.completed_at,
  };

  return (
    <div className="space-y-0">
      {LIFECYCLE.map((state, i) => {
        const reached = i <= currentIndex && !isFailed && !isCancelled;
        const isCurrent = state === task.state;
        const dotColor = reached ? taskStateDot[state] : "bg-gray-700";
        const ts = timestamps[state];

        return (
          <div key={state} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div
                className={`mt-1 flex h-5 w-5 items-center justify-center rounded-full ${dotColor}`}
              >
                {reached ? (
                  isCurrent ? (
                    <Clock size={10} className="text-white" />
                  ) : (
                    <CheckCircle size={10} className="text-white" />
                  )
                ) : (
                  <Circle size={10} className="text-gray-600" />
                )}
              </div>
              {i < LIFECYCLE.length - 1 && (
                <div
                  className={`h-6 w-px ${reached ? "bg-gray-500" : "bg-gray-800"}`}
                />
              )}
            </div>
            <div className="pb-4">
              <span
                className={`text-xs font-medium ${reached ? "text-gray-200" : "text-gray-600"}`}
              >
                {state}
              </span>
              {ts && (
                <p className="text-[10px] text-gray-500">
                  {new Date(ts.endsWith("Z") || ts.includes("+") ? ts : ts + "Z").toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        );
      })}

      {(isFailed || isCancelled) && (
        <div className="flex items-start gap-3">
          <div className="flex flex-col items-center">
            <div
              className={`mt-1 flex h-5 w-5 items-center justify-center rounded-full ${
                isFailed ? "bg-state-failed" : "bg-state-cancelled"
              }`}
            >
              <Circle size={10} className="text-white" />
            </div>
          </div>
          <div>
            <span className="text-xs font-medium text-gray-200">
              {task.state}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
