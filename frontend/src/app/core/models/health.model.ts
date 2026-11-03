export type ComponentState = "connected" | "disconnected" | "error";
export type ReadinessState = "ready" | "unhealthy";

export interface ComponentStatus {
  name: string;
  status: ComponentState;
  latency_ms: number | null;
  error: string | null;
}

export interface HealthLiveResponse {
  status: "live";
  timestamp: string;
  service: string;
  version: string;
}

export interface HealthReadyResponse {
  status: ReadinessState;
  timestamp: string;
  components: Record<string, ComponentStatus>;
}

export interface HealthDashboardState {
  loading: boolean;
  ready: boolean;
  lastChecked: Date | null;
  data: HealthReadyResponse | null;
  error: string | null;
}
