import { Injectable, signal } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable, catchError, of, tap } from "rxjs";
import {
  HealthDashboardState,
  HealthLiveResponse,
  HealthReadyResponse,
} from "../models/health.model";

@Injectable({
  providedIn: "root",
})
export class HealthService {
  private baseUrl = "http://localhost:8000";

  constructor(private http: HttpClient) {}

  state = signal<HealthDashboardState>({
    loading: false,
    ready: false,
    lastChecked: null,
    data: null,
    error: null,
  });

  checkLiveness(): Observable<HealthLiveResponse> {
    return this.http.get<HealthLiveResponse>(`${this.baseUrl}/health/live`);
  }

  checkReadiness(): Observable<HealthReadyResponse> {
    this.state.update((s) => ({ ...s, loading: true, error: null }));

    return this.http.get<HealthReadyResponse>(`${this.baseUrl}/health/ready`).pipe(
      tap((res) => {
        this.state.set({
          loading: false,
          ready: res.status === "ready",
          lastChecked: new Date(),
          data: res,
          error: null,
        });
      }),
      catchError((err: { error?: HealthReadyResponse; message?: string }) => {
        const errorData = err.error && err.error.status ? err.error : null;
        this.state.set({
          loading: false,
          ready: false,
          lastChecked: new Date(),
          data: errorData,
          error: err.message || "Failed to reach health endpoint",
        });
        const fallback: HealthReadyResponse = errorData || {
          status: "unhealthy",
          timestamp: new Date().toISOString(),
          components: {},
        };
        return of(fallback);
      })
    );
  }
}
