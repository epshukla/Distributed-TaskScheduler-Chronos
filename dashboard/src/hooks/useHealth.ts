import { useQuery } from "@tanstack/react-query";
import { fetchHealth, fetchReadiness } from "@/api/health";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 5000,
  });
}

export function useReadiness() {
  return useQuery({
    queryKey: ["readiness"],
    queryFn: fetchReadiness,
    refetchInterval: 10000,
  });
}
