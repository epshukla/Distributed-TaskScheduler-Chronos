import { useState, useEffect } from "react";
import {
  Plus,
  ChevronDown,
  ChevronUp,
  Trash2,
} from "lucide-react";
import { useCreateTask } from "@/hooks/useTasks";
import { fetchTaskTemplates } from "@/api/tasks";
import type { TaskCreate, TaskTemplate } from "@/types/task";

const IMAGE_SUGGESTIONS = [
  "alpine:latest",
  "python:3.12-slim",
  "ubuntu:22.04",
  "node:20-slim",
  "golang:1.22-alpine",
];

const TEMPLATE_ICONS: Record<string, string> = {
  "cpu-stress": "🔥",
  "memory-allocator": "🧠",
  "web-scraper": "🌐",
  "disk-io": "💾",
  "sleep-job": "😴",
  fibonacci: "🔢",
};

const emptyForm: TaskCreate = {
  name: "",
  description: "",
  priority: 5,
  resource_cpu: 0.5,
  resource_memory: 256,
  max_retries: 3,
  image: "alpine:latest",
  command: undefined,
  env_vars: undefined,
  timeout_seconds: 300,
};

export function TaskSubmitForm() {
  const createTask = useCreateTask();
  const [open, setOpen] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [form, setForm] = useState<TaskCreate>({ ...emptyForm });
  const [commandStr, setCommandStr] = useState("");
  const [envRows, setEnvRows] = useState<{ key: string; value: string }[]>([]);
  const [templates, setTemplates] = useState<Record<string, TaskTemplate>>({});
  const [workingDir, setWorkingDir] = useState("");

  useEffect(() => {
    fetchTaskTemplates()
      .then(setTemplates)
      .catch(() => {});
  }, []);

  const applyTemplate = (key: string) => {
    const t = templates[key];
    if (!t) return;
    setForm({
      name: t.name,
      description: t.description,
      priority: 5,
      resource_cpu: t.resource_cpu,
      resource_memory: t.resource_memory,
      max_retries: 3,
      image: t.image,
      command: t.command,
      timeout_seconds: t.timeout_seconds ?? 300,
    });
    setCommandStr(t.command ? t.command.join(" ") : "");
    setEnvRows([]);
    setWorkingDir("");
    setOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.image.trim()) return;

    const payload: TaskCreate = { ...form };

    // Parse command string into array
    if (commandStr.trim()) {
      payload.command = parseCommand(commandStr);
    }

    // Collect env vars
    const envMap: Record<string, string> = {};
    for (const row of envRows) {
      if (row.key.trim()) envMap[row.key.trim()] = row.value;
    }
    if (Object.keys(envMap).length > 0) {
      payload.env_vars = envMap;
    }

    if (workingDir.trim()) {
      payload.working_dir = workingDir.trim();
    }

    createTask.mutate(payload, {
      onSuccess: () => {
        setForm({ ...emptyForm });
        setCommandStr("");
        setEnvRows([]);
        setWorkingDir("");
        setOpen(false);
      },
    });
  };

  if (!open) {
    return (
      <div className="flex flex-col gap-3">
        {/* Template quick-launch cards */}
        {Object.keys(templates).length > 0 && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(templates).map(([key, tmpl]) => (
              <button
                key={key}
                onClick={() => applyTemplate(key)}
                className="flex items-center gap-1.5 rounded-lg border border-surface-100/20 bg-surface-50/30 px-3 py-1.5 text-xs text-gray-300 transition-colors hover:border-accent/40 hover:bg-surface-50/60"
                title={tmpl.description}
              >
                <span>{TEMPLATE_ICONS[key] || "📦"}</span>
                <span>{tmpl.name}</span>
              </button>
            ))}
          </div>
        )}
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-dark"
        >
          <Plus size={16} />
          New Task
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="card w-full space-y-4 border-accent/30"
    >
      {/* Template selector */}
      {Object.keys(templates).length > 0 && (
        <div>
          <label className="mb-1.5 block text-xs text-gray-500">
            Quick Templates
          </label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(templates).map(([key, tmpl]) => (
              <button
                key={key}
                type="button"
                onClick={() => applyTemplate(key)}
                className="flex items-center gap-1.5 rounded-full border border-surface-100/30 px-3 py-1 text-xs text-gray-400 transition-colors hover:border-accent/40 hover:text-gray-200"
              >
                <span>{TEMPLATE_ICONS[key] || "📦"}</span>
                {tmpl.name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {/* Name */}
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-gray-500">Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
            placeholder="my-task"
            required
          />
        </div>

        {/* Image */}
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-gray-500">
            Docker Image
          </label>
          <input
            value={form.image}
            onChange={(e) => setForm({ ...form, image: e.target.value })}
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 font-mono text-sm text-gray-200 outline-none focus:border-accent/50"
            placeholder="python:3.12-slim"
            list="image-suggestions"
            required
          />
          <datalist id="image-suggestions">
            {IMAGE_SUGGESTIONS.map((img) => (
              <option key={img} value={img} />
            ))}
          </datalist>
        </div>

        {/* Command */}
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-gray-500">
            Command
          </label>
          <input
            value={commandStr}
            onChange={(e) => setCommandStr(e.target.value)}
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 font-mono text-sm text-gray-200 outline-none focus:border-accent/50"
            placeholder="python -c print(hello)"
          />
        </div>

        {/* Priority & Timeout */}
        <div>
          <label className="mb-1 block text-xs text-gray-500">Priority</label>
          <input
            type="number"
            min={0}
            max={100}
            value={form.priority}
            onChange={(e) =>
              setForm({ ...form, priority: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-500">
            Timeout (seconds)
          </label>
          <input
            type="number"
            min={1}
            max={3600}
            value={form.timeout_seconds}
            onChange={(e) =>
              setForm({ ...form, timeout_seconds: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>

        {/* CPU & Memory */}
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
            min={32}
            step={32}
            value={form.resource_memory}
            onChange={(e) =>
              setForm({ ...form, resource_memory: Number(e.target.value) })
            }
            className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 text-sm text-gray-200 outline-none focus:border-accent/50"
          />
        </div>
      </div>

      {/* Environment Variables */}
      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="text-xs text-gray-500">
            Environment Variables
          </label>
          <button
            type="button"
            onClick={() =>
              setEnvRows([...envRows, { key: "", value: "" }])
            }
            className="text-xs text-accent hover:text-accent-light"
          >
            + Add
          </button>
        </div>
        {envRows.map((row, i) => (
          <div key={i} className="mb-1 flex gap-2">
            <input
              value={row.key}
              onChange={(e) => {
                const next = [...envRows];
                next[i] = { ...next[i], key: e.target.value };
                setEnvRows(next);
              }}
              placeholder="KEY"
              className="w-1/3 rounded-lg border border-surface-100/30 bg-surface px-2 py-1.5 font-mono text-xs text-gray-200 outline-none focus:border-accent/50"
            />
            <input
              value={row.value}
              onChange={(e) => {
                const next = [...envRows];
                next[i] = { ...next[i], value: e.target.value };
                setEnvRows(next);
              }}
              placeholder="value"
              className="flex-1 rounded-lg border border-surface-100/30 bg-surface px-2 py-1.5 font-mono text-xs text-gray-200 outline-none focus:border-accent/50"
            />
            <button
              type="button"
              onClick={() => setEnvRows(envRows.filter((_, j) => j !== i))}
              className="text-gray-600 hover:text-red-400"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      {/* Advanced options */}
      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300"
      >
        Advanced Options
        {showAdvanced ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {showAdvanced && (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-xs text-gray-500">
              Working Dir
            </label>
            <input
              value={workingDir}
              onChange={(e) => setWorkingDir(e.target.value)}
              className="w-full rounded-lg border border-surface-100/30 bg-surface px-3 py-2 font-mono text-sm text-gray-200 outline-none focus:border-accent/50"
              placeholder="/app"
            />
          </div>
          <div>
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
        </div>
      )}

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

function parseCommand(input: string): string[] {
  // Simple shell-like command parsing
  const result: string[] = [];
  let current = "";
  let inSingle = false;
  let inDouble = false;

  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (ch === "'" && !inDouble) {
      inSingle = !inSingle;
    } else if (ch === '"' && !inSingle) {
      inDouble = !inDouble;
    } else if (ch === " " && !inSingle && !inDouble) {
      if (current) {
        result.push(current);
        current = "";
      }
    } else {
      current += ch;
    }
  }
  if (current) result.push(current);
  return result;
}
