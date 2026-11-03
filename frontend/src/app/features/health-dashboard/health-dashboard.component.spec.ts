import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { HealthDashboardComponent } from "./health-dashboard.component";
import { HealthService } from "../../core/services/health.service";

describe("HealthDashboardComponent", () => {
  let component: HealthDashboardComponent;
  let mockHealthService: {
    checkReadiness: ReturnType<typeof vi.fn>;
    state: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    mockHealthService = {
      checkReadiness: vi.fn().mockReturnValue(of({ status: "ready", components: {} })),
      state: vi.fn().mockReturnValue({
        loading: false,
        ready: true,
        lastChecked: new Date(),
        data: {
          status: "ready",
          components: {
            postgres: { name: "postgres", status: "connected", latency_ms: 1.0, error: null },
          },
        },
        error: null,
      }),
    };

    component = new HealthDashboardComponent(mockHealthService as unknown as HealthService);
  });

  it("should create the component and refresh on init", () => {
    expect(component).toBeTruthy();
    component.ngOnInit();
    expect(mockHealthService.checkReadiness).toHaveBeenCalled();
  });

  it("should extract component keys correctly", () => {
    const keys = component.getComponentKeys({ postgres: {}, redis: {} });
    expect(keys).toEqual(["postgres", "redis"]);
  });

  it("should return empty array when components map is undefined", () => {
    const keys = component.getComponentKeys(undefined);
    expect(keys).toEqual([]);
  });
});
