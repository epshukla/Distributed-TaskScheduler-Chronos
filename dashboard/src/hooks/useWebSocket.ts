import { useContext } from "react";
import { WebSocketContext } from "@/providers/WebSocketProvider";

export function useWebSocket() {
  return useContext(WebSocketContext);
}
