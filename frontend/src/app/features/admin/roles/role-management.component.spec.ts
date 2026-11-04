import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { RoleManagementComponent } from "./role-management.component";
import { RoleService } from "../../../core/services/role.service";

describe("RoleManagementComponent", () => {
  let component: RoleManagementComponent;
  let mockRoleService: { getRoles: ReturnType<typeof vi.fn>; getPermissions: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockRoleService = {
      getRoles: vi.fn().mockReturnValue(of([
        {
          id: "r1",
          code: "ROLE_SUPER_ADMIN",
          name: "Super Administrator",
          description: "Full access",
          is_system: true,
          permissions: ["USER_MANAGE", "ROLE_MANAGE"],
        },
      ])),
      getPermissions: vi.fn().mockReturnValue(of([
        { id: "p1", code: "USER_MANAGE", name: "User Manage", module: "auth", description: null },
      ])),
    };

    component = new RoleManagementComponent(mockRoleService as unknown as RoleService);
  });

  it("should load roles and permissions on init", () => {
    component.ngOnInit();
    expect(component.roles().length).toBe(1);
    expect(component.roles()[0].code).toBe("ROLE_SUPER_ADMIN");
    expect(component.permissions().length).toBe(1);
    expect(component.loading()).toBe(false);
  });
});
