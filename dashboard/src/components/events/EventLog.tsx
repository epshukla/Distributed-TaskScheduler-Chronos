import { useState } from "react";
import { EventFeed } from "./EventFeed";
import type { EventType } from "@/types/events";

const ALL_TYPES: EventType[] = [
  "task_created",
  "task_scheduled",
  "task_state_changed",
  "worker_registered",
  "worker_heartbeat",
  "worker_dead",
];

export function EventLog() {
  const [activeFilters, setActiveFilters] = useState<EventType[]>([]);

  const toggleFilter = (t: EventType) => {
    setActiveFilters((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t],
    );
  };

  const filterTypes =
    activeFilters.length > 0 ? activeFilters : undefined;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {ALL_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => toggleFilter(t)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              activeFilters.includes(t)
                ? "bg-accent text-white"
                : "bg-surface-50 text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.replace(/_/g, " ")}
          </button>
        ))}
        {activeFilters.length > 0 && (
          <button
            onClick={() => setActiveFilters([])}
            className="rounded-full px-3 py-1 text-xs text-gray-500 hover:text-gray-300"
          >
            Clear
          </button>
        )}
      </div>
      <EventFeed maxEvents={200} filterTypes={filterTypes} />
    </div>
  );
}
