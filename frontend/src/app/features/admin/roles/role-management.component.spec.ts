import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { FormBuilder } from "@angular/forms";
import { RoleManagementComponent } from "./role-management.component";
import { RoleService } from "../../../core/services/role.service";

describe("RoleManagementComponent", () => {
  let component: RoleManagementComponent;
  let mockRoleService: {
    getRoles: ReturnType<typeof vi.fn>;
    getPermissions: ReturnType<typeof vi.fn>;
    createRole: ReturnType<typeof vi.fn>;
    getRoleUsers: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    mockRoleService = {
      getRoles: vi.fn().mockReturnValue(of([
        {
          id: "r1",
          code: "ROLE_SUPER_ADMIN",
          name: "مدیر ارشد",
          description: "دسترسی کامل",
          is_system: true,
          permissions: ["USER_MANAGE", "ROLE_MANAGE"],
          assigned_user_count: 1,
        },
      ])),
      getPermissions: vi.fn().mockReturnValue(of([
        { id: "p1", code: "USER_MANAGE", name: "مدیریت کاربران", module: "admin", description: null },
      ])),
      createRole: vi.fn().mockReturnValue(of({
        id: "r2",
        code: "ROLE_AUDIT",
        name: "حسابرس",
        description: null,
        is_system: false,
        permissions: [],
        assigned_user_count: 0,
      })),
      getRoleUsers: vi.fn().mockReturnValue(of([
        { id: "u1", username: "admin", full_name: "مدیر", email: "a@m.com", is_active: true },
      ])),
    };

    component = new RoleManagementComponent(
      mockRoleService as unknown as RoleService,
      new FormBuilder()
    );
  });

  it("should load roles and permissions on init", () => {
    component.ngOnInit();
    expect(component.roles().length).toBe(1);
    expect(component.roles()[0].code).toBe("ROLE_SUPER_ADMIN");
    expect(component.permissions().length).toBe(1);
    expect(component.loading()).toBe(false);
  });

  it("should open and close create role modal", () => {
    component.openCreateModal();
    expect(component.isCreateModalOpen()).toBe(true);

    component.closeCreateModal();
    expect(component.isCreateModalOpen()).toBe(false);
  });

  it("should submit new role when form is valid", () => {
    component.roleForm.patchValue({
      code: "ROLE_AUDIT",
      name: "حسابرس",
    });
    component.submitNewRole();

    expect(mockRoleService.createRole).toHaveBeenCalled();
    expect(component.roles().length).toBe(1);
  });

  it("should fetch assigned users when inspecting role", () => {
    const role = {
      id: "r1",
      code: "ROLE_SUPER_ADMIN",
      name: "مدیر ارشد",
      description: null,
      is_system: true,
      permissions: [],
      assigned_user_count: 1,
    };
    component.inspectRoleUsers(role);

    expect(component.isUserModalOpen()).toBe(true);
    expect(mockRoleService.getRoleUsers).toHaveBeenCalledWith("r1");
    expect(component.roleUsers().length).toBe(1);
  });
});
