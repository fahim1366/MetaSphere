import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { AuditLogComponent } from "./audit-log.component";
import { AuditService } from "../../../core/services/audit.service";

describe("AuditLogComponent", () => {
  let component: AuditLogComponent;
  let mockAuditService: { getAuditLogs: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockAuditService = {
      getAuditLogs: vi.fn().mockReturnValue(of([
        {
          id: "log-1",
          event_type: "LOGIN_SUCCESS",
          user_id: "u1",
          actor_id: null,
          target_resource: "alice",
          status: "SUCCESS",
          ip_address: "127.0.0.1",
          timestamp: "2026-11-04T12:00:00Z",
          details: { role: "ADMIN" },
        },
      ])),
    };

    component = new AuditLogComponent(mockAuditService as unknown as AuditService);
  });

  it("should load audit logs on init", () => {
    component.ngOnInit();
    expect(component.logs().length).toBe(1);
    expect(component.logs()[0].event_type).toBe("LOGIN_SUCCESS");
    expect(component.loading()).toBe(false);
  });

  it("should style event badges appropriately", () => {
    expect(component.getEventBadgeClass("LOGIN_SUCCESS")).toContain("bg-emerald-50");
    expect(component.getEventBadgeClass("LOGIN_FAILED")).toContain("bg-rose-50");
    expect(component.getEventBadgeClass("USER_CREATED")).toContain("bg-blue-50");
  });
});
