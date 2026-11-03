import { HttpClient } from "@angular/common/http";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { of, throwError } from "rxjs";
import { HealthService } from "./health.service";
import { HealthReadyResponse } from "../models/health.model";

describe("HealthService", () => {
  let service: HealthService;
  let mockHttpClient: { get: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockHttpClient = {
      get: vi.fn(),
    };
    service = new HealthService(mockHttpClient as unknown as HttpClient);
  });

  it("should initialize with default state", () => {
    const s = service.state();
    expect(s.loading).toBe(false);
    expect(s.ready).toBe(false);
    expect(s.data).toBeNull();
  });

  it("should update state to ready when health check succeeds", () => {
    const mockResponse: HealthReadyResponse = {
      status: "ready",
      timestamp: "2026-11-02T12:00:00Z",
      components: {
        postgres: { name: "postgres", status: "connected", latency_ms: 1.2, error: null },
        redis: { name: "redis", status: "connected", latency_ms: 0.5, error: null },
      },
    };
    mockHttpClient.get.mockReturnValue(of(mockResponse));

    service.checkReadiness().subscribe((res) => {
      expect(res.status).toBe("ready");
      const s = service.state();
      expect(s.loading).toBe(false);
      expect(s.ready).toBe(true);
      expect(s.data?.components["postgres"].status).toBe("connected");
    });
  });

  it("should handle error response and update state to unhealthy", () => {
    mockHttpClient.get.mockReturnValue(
      throwError(() => ({
        error: {
          status: "unhealthy",
          timestamp: "2026-11-02T12:00:00Z",
          components: {
            postgres: { name: "postgres", status: "disconnected", latency_ms: 2.0, error: "timeout" },
          },
        },
      }))
    );

    service.checkReadiness().subscribe((res) => {
      expect(res.status).toBe("unhealthy");
      const s = service.state();
      expect(s.loading).toBe(false);
      expect(s.ready).toBe(false);
    });
  });
});
