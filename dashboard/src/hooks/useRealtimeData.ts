import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useWebSocket } from "./useWebSocket";
import type { WebSocketEvent } from "@/types/events";

export function useRealtimeData() {
  const { subscribe } = useWebSocket();
  const queryClient = useQueryClient();

  useEffect(() => {
    const unsubscribe = subscribe((event: WebSocketEvent) => {
      switch (event.type) {
        case "task_created":
        case "task_state_changed":
        case "task_scheduled":
          queryClient.invalidateQueries({ queryKey: ["tasks"] });
          queryClient.invalidateQueries({ queryKey: ["stats"] });
          break;
        case "worker_registered":
        case "worker_dead":
        case "worker_heartbeat":
          queryClient.invalidateQueries({ queryKey: ["workers"] });
          queryClient.invalidateQueries({ queryKey: ["stats"] });
          break;
      }
    });
    return unsubscribe;
  }, [subscribe, queryClient]);
}
