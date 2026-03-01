import {
  ListTodo,
  Server,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
} from "lucide-react";
import { PageWrapper } from "@/components/layout/PageWrapper";
import { KPICard } from "@/components/common/KPICard";
import { ClusterTopology } from "@/components/topology/ClusterTopology";
import { StateDistributionChart } from "@/components/metrics/StateDistributionChart";
import { ThroughputChart } from "@/components/metrics/ThroughputChart";
import { EventFeed } from "@/components/events/EventFeed";
import { useTasks } from "@/hooks/useTasks";
import { useWorkers } from "@/hooks/useWorkers";
import { useStats } from "@/hooks/useStats";
import { useMetricsHistory } from "@/hooks/useMetricsHistory";
import { TaskState } from "@/types/task";

export function Overview() {
  const { data: allTasks } = useTasks({ page_size: 200 });
  const { data: workers } = useWorkers();
  const { data: stats } = useStats();
  const { taskThroughput } = useMetricsHistory();

  const tasks = allTasks?.items ?? [];
  const stateCounts = stats?.state_counts ?? {};
  const totalTasks = allTasks?.total ?? 0;
  const running = stateCounts["RUNNING"] ?? 0;
  const completed = stateCounts["COMPLETED"] ?? 0;
  const failed = stateCounts["FAILED"] ?? 0;
  const pending = stateCounts["PENDING"] ?? 0;
  const activeWorkers = (workers ?? []).filter((w) => w.status === "ACTIVE").length;
  const totalWorkers = workers?.length ?? 0;

  return (
    <PageWrapper title="Cluster Overview" subtitle="Real-time system status">
      {/* KPI Cards */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <KPICard
          title="Total Tasks"
          value={totalTasks}
          icon={ListTodo}
          iconColor="text-blue-400"
        />
        <KPICard
          title="Running"
          value={running}
          icon={Zap}
          iconColor="text-purple-400"
        />
        <KPICard
          title="Completed"
          value={completed}
          icon={CheckCircle}
          iconColor="text-emerald-400"
        />
        <KPICard
          title="Failed"
          value={failed}
          icon={AlertTriangle}
          iconColor="text-red-400"
        />
        <KPICard
          title="Workers"
          value={activeWorkers}
          icon={Server}
          iconColor="text-emerald-400"
          suffix={`/ ${totalWorkers}`}
        />
        <KPICard
          title="Pending"
          value={pending}
          icon={Clock}
          iconColor="text-yellow-400"
        />
      </div>

      {/* Topology */}
      <div className="mb-6">
        <h3 className="mb-3 text-sm font-medium text-gray-400">
          Cluster Topology
        </h3>
        <ClusterTopology />
      </div>

      {/* Charts + Feed */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-1">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Task Distribution
          </h3>
          <StateDistributionChart tasks={tasks} />
        </div>
        <div className="card lg:col-span-1">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Completions (per 5s)
          </h3>
          <ThroughputChart data={taskThroughput} />
        </div>
        <div className="card lg:col-span-1">
          <h3 className="mb-3 text-sm font-medium text-gray-400">
            Live Events
          </h3>
          <EventFeed compact maxEvents={30} />
        </div>
      </div>
    </PageWrapper>
  );
}
