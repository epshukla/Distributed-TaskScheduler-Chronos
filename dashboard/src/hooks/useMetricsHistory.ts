import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "./useWebSocket";
import { useStats } from "./useStats";
import type { WebSocketEvent } from "@/types/events";

interface MetricPoint {
  timestamp: number;
  value: number;
  label?: string;
}

export function useMetricsHistory(maxPoints = 60) {
  const { subscribe, isConnected } = useWebSocket();
  const { data: stats } = useStats();
  const [taskThroughput, setTaskThroughput] = useState<MetricPoint[]>([]);
  const [workerUtilization, setWorkerUtilization] = useState<
    Map<string, MetricPoint[]>
  >(new Map());

  // Track completions via WebSocket
  const wsCompletionCountRef = useRef(0);

  // Track completions via polling fallback
  const prevCompletedRef = useRef<number | null>(null);
  const pollCompletionCountRef = useRef(0);

  const addPoint = useCallback(
    (
      setter: React.Dispatch<React.SetStateAction<MetricPoint[]>>,
      point: MetricPoint,
    ) => {
      setter((prev) => {
        const next = [...prev, point];
        return next.length > maxPoints ? next.slice(-maxPoints) : next;
      });
    },
    [maxPoints],
  );

  // Polling fallback: detect completed count changes from stats
  useEffect(() => {
    if (!stats) return;
    const completed = stats.state_counts["COMPLETED"] ?? 0;
    if (prevCompletedRef.current !== null) {
      const delta = completed - prevCompletedRef.current;
      if (delta > 0) {
        pollCompletionCountRef.current += delta;
      }
    }
    prevCompletedRef.current = completed;
  }, [stats]);

  // Sample throughput every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // Use WS count if connected, otherwise polling count
      const count = isConnected
        ? wsCompletionCountRef.current
        : pollCompletionCountRef.current;

      addPoint(setTaskThroughput, {
        timestamp: Date.now(),
        value: count,
      });
      wsCompletionCountRef.current = 0;
      pollCompletionCountRef.current = 0;
    }, 5000);

    return () => clearInterval(interval);
  }, [addPoint, isConnected]);

  // WebSocket event handler
  useEffect(() => {
    const unsubscribe = subscribe((event: WebSocketEvent) => {
      if (
        event.type === "task_state_changed" &&
        "to_state" in event.data &&
        event.data.to_state === "COMPLETED"
      ) {
        wsCompletionCountRef.current++;
      }

      if (event.type === "worker_heartbeat" && "worker_id" in event.data) {
        const { worker_id, cpu_available, cpu_total, hostname } =
          event.data as {
            worker_id: string;
            cpu_available: number;
            cpu_total: number;
            hostname: string;
          };
        const utilization =
          cpu_total > 0
            ? Math.max(0, ((cpu_total - cpu_available) / cpu_total) * 100)
            : 0;

        setWorkerUtilization((prev) => {
          const next = new Map(prev);
          const points = next.get(worker_id) || [];
          const updated = [
            ...points,
            { timestamp: Date.now(), value: utilization, label: hostname },
          ];
          next.set(
            worker_id,
            updated.length > maxPoints ? updated.slice(-maxPoints) : updated,
          );
          return next;
        });
      }
    });
    return unsubscribe;
  }, [subscribe, maxPoints]);

  return { taskThroughput, workerUtilization };
}
