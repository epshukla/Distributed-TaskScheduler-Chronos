import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  type Node,
  type Edge,
  type NodeTypes,
  type EdgeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useWorkers } from "@/hooks/useWorkers";
import { useHealth } from "@/hooks/useHealth";
import { useStats } from "@/hooks/useStats";
import { MasterNode } from "./MasterNode";
import { QueueNode } from "./QueueNode";
import { WorkerNode } from "./WorkerNode";
import { AnimatedEdge } from "./AnimatedEdge";
import { StaticEdge } from "./StaticEdge";

const nodeTypes: NodeTypes = {
  master: MasterNode as unknown as NodeTypes["master"],
  queue: QueueNode as unknown as NodeTypes["queue"],
  worker: WorkerNode as unknown as NodeTypes["worker"],
};

const edgeTypes: EdgeTypes = {
  animated: AnimatedEdge as unknown as EdgeTypes["animated"],
  static: StaticEdge as unknown as EdgeTypes["static"],
};

export function ClusterTopology() {
  const { data: workers } = useWorkers();
  const { data: health } = useHealth();
  const { data: stats } = useStats();

  const queueDepth = stats?.queue_depth ?? 0;
  const pipelineActive = stats?.pipeline_active ?? 0;
  const workerTaskCounts = stats?.worker_task_counts ?? {};
  const stateCounts = stats?.state_counts ?? {};
  const pendingCount = stateCounts["PENDING"] ?? 0;
  const scheduledCount = stateCounts["SCHEDULED"] ?? 0;
  const runningCount = stateCounts["RUNNING"] ?? 0;

  // Tasks actively in the pipeline (waiting in queue or being dispatched)
  const inQueue = queueDepth + pendingCount + scheduledCount;
  // Any active work happening
  const hasActivity = pipelineActive > 0;

  const { nodes, edges } = useMemo(() => {
    const n: Node[] = [];
    const e: Edge[] = [];

    n.push({
      id: "master",
      type: "master",
      position: { x: 300, y: 20 },
      data: {
        label: "Chronos Master",
        isLeader: health?.is_leader ?? false,
        version: health?.node_id ?? "",
      },
      draggable: true,
    });

    n.push({
      id: "queue",
      type: "queue",
      position: { x: 300, y: 140 },
      data: {
        label: "Priority Queue",
        depth: inQueue,
        maxDepth: 100,
      },
      draggable: true,
    });

    // Master → Queue: animate when tasks are entering the pipeline
    e.push({
      id: "master-queue",
      source: "master",
      target: "queue",
      type: pendingCount > 0 || queueDepth > 0 ? "animated" : "static",
    });

    const workerList = workers ?? [];
    const spacing = 220;
    const totalWidth = (workerList.length - 1) * spacing;
    const startX = 300 - totalWidth / 2;

    workerList.forEach((w, i) => {
      const nodeId = `worker-${w.id}`;
      const taskCount = workerTaskCounts[w.id] ?? 0;
      const cpuUsed = Math.max(0, w.cpu_total - w.cpu_available);
      const memUsed = Math.max(0, w.memory_total - w.memory_available);

      n.push({
        id: nodeId,
        type: "worker",
        position: { x: startX + i * spacing, y: 290 },
        data: {
          hostname: w.hostname,
          status: w.status,
          cpuUsed,
          cpuTotal: w.cpu_total,
          memUsed,
          memTotal: w.memory_total,
          taskCount,
        },
        draggable: true,
      });

      // Queue → Worker: animate only when this specific worker is processing tasks
      e.push({
        id: `queue-${nodeId}`,
        source: "queue",
        target: nodeId,
        type: taskCount > 0 ? "animated" : "static",
      });
    });

    return { nodes: n, edges: e };
  }, [workers, health, inQueue, pendingCount, queueDepth, workerTaskCounts]);

  return (
    <div className="h-[420px] rounded-xl border border-surface-100/20 bg-surface-50/30">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="#1e293b" gap={20} />
      </ReactFlow>
    </div>
  );
}
