import { useState } from "react";
import { Plus } from "lucide-react";
import { useCreateTask } from "@/hooks/useTasks";
import type { TaskCreate } from "@/types/task";

export function TaskSubmitForm() {
  const createTask = useCreateTask();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<TaskCreate>({
    name: "",
    description: "",
    priority: 5,
    resource_cpu: 0.5,
    resource_memory: 256,
    max_retries: 3,
    duration_seconds: 10,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    createTask.mutate(form, {
      onSuccess: () => {
        setForm({
          name: "",
          description: "",
          priority: 5,
          resource_cpu: 0.5,
          resource_memory: 256,
          max_retries: 3,
          duration_seconds: 10,
        });
        setOpen(false);
      },
    });
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-dark"
      >
        <Plus size={16} />
        New Task
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="card w-full space-y-4 border-accent/30"
    >
      <div className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-gray-500">Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
            placeholder="task-name"
            required
          />
        </div>
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-gray-500">
            Description
          </label>
          <input
            value={form.description || ""}
            onChange={(e) =>
              setForm({ ...form, description: e.target.value })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
            placeholder="Optional description"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-500">
            Priority (1-10)
          </label>
          <input
            type="number"
            min={1}
            max={10}
            value={form.priority}
            onChange={(e) =>
              setForm({ ...form, priority: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-500">
            Duration (seconds)
          </label>
          <input
            type="number"
            min={1}
            value={form.duration_seconds}
            onChange={(e) =>
              setForm({ ...form, duration_seconds: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-500">
            CPU (cores)
          </label>
          <input
            type="number"
            min={0.1}
            step={0.1}
            value={form.resource_cpu}
            onChange={(e) =>
              setForm({ ...form, resource_cpu: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-500">
            Memory (MB)
          </label>
          <input
            type="number"
            min={64}
            step={64}
            value={form.resource_memory}
            onChange={(e) =>
              setForm({ ...form, resource_memory: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={createTask.isPending}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-dark disabled:opacity-50"
        >
          {createTask.isPending ? "Creating..." : "Create Task"}
        </button>
      </div>
    </form>
  );
}
