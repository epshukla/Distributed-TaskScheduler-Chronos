import { useState } from "react";
import { Zap } from "lucide-react";
import { useCreateTask } from "@/hooks/useTasks";
import toast from "react-hot-toast";

const NAMES = [
  "data-pipeline",
  "model-training",
  "image-resize",
  "log-aggregator",
  "cache-rebuild",
  "report-gen",
  "etl-job",
  "health-check",
  "backup-snap",
  "index-rebuild",
];

export function BatchSubmitButton() {
  const createTask = useCreateTask();
  const [submitting, setSubmitting] = useState(false);

  const handleBatch = async () => {
    setSubmitting(true);
    const count = 10;
    let created = 0;

    for (let i = 0; i < count; i++) {
      const name = `${NAMES[Math.floor(Math.random() * NAMES.length)]}-${Date.now().toString(36).slice(-4)}`;
      try {
        await createTask.mutateAsync({
          name,
          priority: Math.floor(Math.random() * 10) + 1,
          resource_cpu: +(Math.random() * 1.5 + 0.1).toFixed(1),
          resource_memory: Math.floor(Math.random() * 512) + 64,
          duration_seconds: Math.floor(Math.random() * 20) + 5,
          max_retries: 3,
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
      {submitting ? "Submitting..." : "Batch (10)"}
    </button>
  );
}
