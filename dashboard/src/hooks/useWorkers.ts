import { useQuery } from "@tanstack/react-query";
import { fetchWorkers } from "@/api/workers";

export function useWorkers(status?: string) {
  return useQuery({
    queryKey: ["workers", status],
    queryFn: () => fetchWorkers(status),
  });
}
