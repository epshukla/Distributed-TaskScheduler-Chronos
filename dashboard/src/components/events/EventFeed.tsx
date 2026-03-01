import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { EventCard } from "./EventCard";
import type { WebSocketEvent, EventType } from "@/types/events";
import { Pause, Play } from "lucide-react";

interface EventFeedProps {
  maxEvents?: number;
  filterTypes?: EventType[];
  compact?: boolean;
}

export function EventFeed({
  maxEvents = 50,
  filterTypes,
  compact = false,
}: EventFeedProps) {
  const { subscribe } = useWebSocket();
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [paused, setPaused] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      if (pausedRef.current) return;
      if (filterTypes && !filterTypes.includes(event.type)) return;
      // Skip heartbeats in compact mode to reduce noise
      if (compact && event.type === "worker_heartbeat") return;
      setEvents((prev) => {
        const next = [event, ...prev];
        return next.length > maxEvents ? next.slice(0, maxEvents) : next;
      });
    },
    [maxEvents, filterTypes, compact],
  );

  useEffect(() => {
    return subscribe(handleEvent);
  }, [subscribe, handleEvent]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-500">
          Live Events ({events.length})
        </span>
        <button
          onClick={() => setPaused(!paused)}
          className="flex items-center gap-1 rounded px-2 py-0.5 text-[10px] text-gray-500 hover:bg-surface-50 hover:text-gray-300"
        >
          {paused ? <Play size={10} /> : <Pause size={10} />}
          {paused ? "Resume" : "Pause"}
        </button>
      </div>
      <div
        ref={containerRef}
        className={`space-y-1 overflow-auto ${compact ? "max-h-80" : "max-h-[600px]"}`}
      >
        {events.length === 0 ? (
          <p className="py-8 text-center text-xs text-gray-600">
            Waiting for events...
          </p>
        ) : (
          events.map((event, i) => <EventCard key={i} event={event} />)
        )}
      </div>
    </div>
  );
}
