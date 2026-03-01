import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Copy, Check } from "lucide-react";
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
        className="fixed right-0 top-0 z-50 flex h-full w-[560px] flex-col border-l border-surface-100/20 bg-surface"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-surface-100/20 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-100">{task.name}</h3>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-surface-50"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content - scrollable */}
        <div className="flex-1 overflow-auto p-6 space-y-6">
          {/* Status + Priority */}
          <div className="flex items-center gap-3">
            <StatusBadge state={task.state} size="md" />
            <PriorityBadge priority={task.priority} />
            <ExitCodeBadge exitCode={task.exit_code} error={task.error} />
          </div>

          <TaskStateTimeline task={task} />

          {/* Container Info */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium uppercase tracking-wider text-gray-500">
              Container Info
            </h4>
            <DetailRow label="Image" value={task.image} mono />
            {task.command && (
              <div>
                <span className="text-xs text-gray-500">Command</span>
                <pre className="mt-1 rounded-lg bg-black/50 p-2 text-xs text-gray-300 overflow-x-auto">
                  {task.command.join(" ")}
                </pre>
              </div>
            )}
            {task.container_id && (
              <DetailRow
                label="Container ID"
                value={task.container_id.slice(0, 12)}
                mono
                copyValue={task.container_id}
              />
            )}
            <DetailRow label="Timeout" value={`${task.timeout_seconds}s`} />
          </div>

          {/* Environment Variables */}
          {task.env_vars && Object.keys(task.env_vars).length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">
                Environment Variables
              </h4>
              <div className="rounded-lg bg-black/30 p-2">
                {Object.entries(task.env_vars).map(([k, v]) => (
                  <div key={k} className="flex gap-2 text-xs">
                    <span className="font-mono text-blue-400">{k}</span>
                    <span className="text-gray-600">=</span>
                    <span className="font-mono text-gray-400">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Details */}
          <div className="space-y-3">
            <h4 className="text-xs font-medium uppercase tracking-wider text-gray-500">
              Details
            </h4>
            <DetailRow label="ID" value={task.id} mono copyValue={task.id} />
            {task.description && (
              <DetailRow label="Description" value={task.description} />
            )}
            <DetailRow
              label="Resources"
              value={`${task.resource_cpu} CPU / ${task.resource_memory} MB`}
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
                  <span className="text-red-400 text-xs break-all">{task.error}</span>
                }
              />
            )}
          </div>

          {/* Log Terminal */}
          <LogTerminal task={task} />

          {/* Cancel button */}
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

function ExitCodeBadge({
  exitCode,
  error,
}: {
  exitCode: number | null;
  error: string | null;
}) {
  if (exitCode === null) return null;

  const isOOM = error?.includes("OOM");
  const isTimeout = error?.includes("Timeout");

  let bgClass = "bg-emerald-500/20 text-emerald-400";
  let label = `Exit ${exitCode}`;

  if (isOOM) {
    bgClass = "bg-yellow-500/20 text-yellow-400";
    label = "OOM Killed";
  } else if (isTimeout) {
    bgClass = "bg-red-500/20 text-red-400";
    label = "Timeout";
  } else if (exitCode !== 0) {
    bgClass = "bg-red-500/20 text-red-400";
    label = `Exit ${exitCode}`;
  }

  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${bgClass}`}>
      {label}
    </span>
  );
}

function LogTerminal({ task }: { task: Task }) {
  const [activeTab, setActiveTab] = useState<"stdout" | "stderr">("stdout");
  const [liveLines, setLiveLines] = useState<string[]>([]);
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isRunning = task.state === TaskState.RUNNING;
  const isTerminal = [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED].includes(
    task.state as TaskState,
  );

  // Live log streaming for running tasks
  useEffect(() => {
    if (!isRunning) return;

    setStreaming(true);
    setLiveLines([]);
    const eventSource = new EventSource(
      `/api/v1/tasks/${task.id}/logs?follow=true`,
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.line !== undefined) {
          setLiveLines((prev) => [...prev.slice(-500), data.line]);
        }
      } catch {
        // ignore parse errors
      }
    };

    eventSource.addEventListener("done", () => {
      eventSource.close();
      setStreaming(false);
    });

    eventSource.onerror = () => {
      eventSource.close();
      setStreaming(false);
    };

    return () => {
      eventSource.close();
      setStreaming(false);
    };
  }, [task.id, isRunning]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [liveLines, task.stdout, task.stderr, activeTab]);

  const content =
    isRunning && liveLines.length > 0
      ? liveLines.join("\n")
      : activeTab === "stdout"
        ? task.stdout || ""
        : task.stderr || "";

  const hasContent = content.trim().length > 0 || liveLines.length > 0;

  if (!hasContent && !isRunning) return null;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h4 className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {isRunning ? "Live Logs" : "Output"}
        </h4>
        <div className="flex gap-1">
          {isTerminal && (
            <>
              <TabButton
                active={activeTab === "stdout"}
                onClick={() => setActiveTab("stdout")}
                label="STDOUT"
              />
              <TabButton
                active={activeTab === "stderr"}
                onClick={() => setActiveTab("stderr")}
                label="STDERR"
              />
            </>
          )}
          {isRunning && streaming && (
            <span className="flex items-center gap-1 text-[10px] text-emerald-400">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              Streaming
            </span>
          )}
          <CopyButton text={content} />
        </div>
      </div>
      <div
        ref={scrollRef}
        className="max-h-64 overflow-auto rounded-lg bg-black p-3 font-mono text-xs leading-relaxed text-gray-300"
      >
        {content ? (
          <pre className="whitespace-pre-wrap break-all">{content}</pre>
        ) : (
          <span className="text-gray-600 italic">
            {isRunning ? "Waiting for output..." : "No output"}
          </span>
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded px-2 py-0.5 text-[10px] font-medium ${
        active
          ? "bg-surface-100/30 text-gray-200"
          : "text-gray-500 hover:text-gray-300"
      }`}
    >
      {label}
    </button>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="rounded p-1 text-gray-500 hover:text-gray-300"
      title="Copy to clipboard"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
    </button>
  );
}

function DetailRow({
  label,
  value,
  mono,
  copyValue,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  copyValue?: string;
}) {
  const [copied, setCopied] = useState(false);

  return (
    <div className="flex justify-between items-start gap-4">
      <span className="text-xs text-gray-500 shrink-0">{label}</span>
      <div className="flex items-center gap-1">
        <span
          className={`text-sm text-gray-300 text-right ${mono ? "font-mono text-xs" : ""}`}
        >
          {value}
        </span>
        {copyValue && (
          <button
            onClick={() => {
              navigator.clipboard.writeText(copyValue);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
            className="text-gray-600 hover:text-gray-400"
          >
            {copied ? <Check size={10} /> : <Copy size={10} />}
          </button>
        )}
      </div>
    </div>
  );
}
