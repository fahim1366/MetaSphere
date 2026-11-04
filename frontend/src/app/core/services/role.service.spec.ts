import { HttpClient } from "@angular/common/http";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { RoleService } from "./role.service";

describe("RoleService", () => {
  let service: RoleService;
  let mockHttpClient: { get: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockHttpClient = {
      get: vi.fn(),
    };
    service = new RoleService(mockHttpClient as unknown as HttpClient);
  });

  it("should fetch roles list", () => {
    mockHttpClient.get.mockReturnValue(of([{ id: "r1", code: "ROLE_ADMIN", name: "Admin", is_system: true, permissions: [] }]));

    service.getRoles().subscribe((roles) => {
      expect(roles.length).toBe(1);
      expect(roles[0].code).toBe("ROLE_ADMIN");
    });
  });

  it("should fetch permissions list", () => {
    mockHttpClient.get.mockReturnValue(of([{ id: "p1", code: "USER_MANAGE", name: "User Manage", module: "auth", description: null }]));

    service.getPermissions().subscribe((perms) => {
      expect(perms.length).toBe(1);
      expect(perms[0].code).toBe("USER_MANAGE");
    });
  });
});
