import { PageWrapper } from "@/components/layout/PageWrapper";
import { ThroughputChart } from "@/components/metrics/ThroughputChart";
import { UtilizationChart } from "@/components/metrics/UtilizationChart";
import { LatencyHistogram } from "@/components/metrics/LatencyHistogram";
import { HeatmapGrid } from "@/components/metrics/HeatmapGrid";
import { useMetricsHistory } from "@/hooks/useMetricsHistory";
import { useTasks } from "@/hooks/useTasks";
import { useWorkers } from "@/hooks/useWorkers";

export function Metrics() {
  const { taskThroughput, workerUtilization } = useMetricsHistory();
  const { data: allTasks } = useTasks({ page_size: 200 });
  const { data: workers } = useWorkers();

  return (
    <PageWrapper title="Metrics" subtitle="System performance analytics">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Completions (per 5s)
          </h3>
          <ThroughputChart data={taskThroughput} />
        </div>
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Worker CPU Utilization
          </h3>
          <UtilizationChart workerUtilization={workerUtilization} />
        </div>
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Scheduling Latency Distribution
          </h3>
          <LatencyHistogram tasks={allTasks?.items ?? []} />
        </div>
        <div className="card">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Resource Heatmap
          </h3>
          <HeatmapGrid workers={workers ?? []} />
        </div>
      </div>
    </PageWrapper>
  );
}
