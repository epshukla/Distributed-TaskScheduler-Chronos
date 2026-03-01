import { useState } from "react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { WorkerGrid } from "@/components/workers/WorkerGrid";
import { WorkerStatus } from "@/types/worker";

const filters = ["All", ...Object.values(WorkerStatus)];

export function Workers() {
  const [statusFilter, setStatusFilter] = useState("All");

  return (
    <PageWrapper title="Workers" subtitle="Monitor worker nodes and resources">
      <div className="mb-4 flex flex-wrap gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === f
                ? "bg-accent text-white"
                : "bg-surface-50 text-gray-400 hover:text-gray-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      <WorkerGrid
        statusFilter={statusFilter === "All" ? undefined : statusFilter}
      />
    </PageWrapper>
  );
}
