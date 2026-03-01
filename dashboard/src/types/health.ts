export interface HealthResponse {
  status: string;
  is_leader: boolean;
  uptime_seconds: number;
  node_id: string;
}

export interface ReadinessResponse {
  status: string;
  postgres: string;
  redis: string;
  etcd: string;
}
