import { useState } from "react";
import { Zap } from "lucide-react";
import { useCreateTask } from "@/hooks/useTasks";
import toast from "react-hot-toast";

const BATCH_TASKS = [
  {
    name: "batch-sleep",
    image: "alpine:latest",
    command: ["sleep", "10"],
    resource_cpu: 0.25,
    resource_memory: 32,
  },
  {
    name: "batch-echo",
    image: "alpine:latest",
    command: ["sh", "-c", "echo 'Hello from Chronos!' && date"],
    resource_cpu: 0.25,
    resource_memory: 32,
  },
  {
    name: "batch-md5",
    image: "alpine:latest",
    command: ["sh", "-c", "dd if=/dev/urandom bs=1M count=10 | md5sum"],
    resource_cpu: 0.5,
    resource_memory: 64,
  },
  {
    name: "batch-python",
    image: "python:3.12-slim",
    command: ["python", "-c", "print(sum(range(1000000)))"],
    resource_cpu: 0.5,
    resource_memory: 128,
  },
  {
    name: "batch-ls",
    image: "alpine:latest",
    command: ["ls", "-la", "/"],
    resource_cpu: 0.25,
    resource_memory: 32,
  },
];

export function BatchSubmitButton() {
  const createTask = useCreateTask();
  const [submitting, setSubmitting] = useState(false);

  const handleBatch = async () => {
    setSubmitting(true);
    const count = 5;
    let created = 0;

    for (let i = 0; i < count; i++) {
      const tmpl = BATCH_TASKS[i % BATCH_TASKS.length];
      const suffix = Date.now().toString(36).slice(-4);
      try {
        await createTask.mutateAsync({
          name: `${tmpl.name}-${suffix}`,
          image: tmpl.image,
          command: tmpl.command,
          priority: Math.floor(Math.random() * 10) + 1,
          resource_cpu: tmpl.resource_cpu,
          resource_memory: tmpl.resource_memory,
          max_retries: 2,
          timeout_seconds: 120,
        });
        created++;
      } catch {
        // individual failure, continue
      }
    }

    toast.success(`Batch submitted: ${created}/${count} tasks`);
    setSubmitting(false);
  };

  return (
    <button
      onClick={handleBatch}
      disabled={submitting}
      className="flex items-center gap-2 rounded-lg border border-accent/30 px-4 py-2 text-sm font-medium text-accent-light transition-colors hover:bg-accent/10 disabled:opacity-50"
    >
      <Zap size={14} />
      {submitting ? "Submitting..." : "Batch (5)"}
    </button>
  );
}
