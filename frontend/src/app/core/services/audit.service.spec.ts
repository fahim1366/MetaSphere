import { HttpClient } from "@angular/common/http";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { AuditService } from "./audit.service";

describe("AuditService", () => {
  let service: AuditService;
  let mockHttpClient: { get: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockHttpClient = {
      get: vi.fn(),
    };
    service = new AuditService(mockHttpClient as unknown as HttpClient);
  });

  it("should query security audit events with pagination params", () => {
    mockHttpClient.get.mockReturnValue(of([
      {
        id: "a1",
        event_type: "LOGIN_SUCCESS",
        user_id: "u1",
        actor_id: null,
        target_resource: "alice",
        status: "SUCCESS",
        ip_address: "127.0.0.1",
        timestamp: "2026-11-04T12:00:00Z",
        details: null,
      },
    ]));

    service.getAuditLogs(20, 0).subscribe((logs) => {
      expect(logs.length).toBe(1);
      expect(logs[0].event_type).toBe("LOGIN_SUCCESS");
    });
  });
});
