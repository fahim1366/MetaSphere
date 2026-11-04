import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { FormBuilder } from "@angular/forms";
import { UserManagementComponent } from "./user-management.component";
import { UserService } from "../../../core/services/user.service";
import { RoleService } from "../../../core/services/role.service";

describe("UserManagementComponent", () => {
  let component: UserManagementComponent;
  let mockUserService: { getUsers: ReturnType<typeof vi.fn>; createUser: ReturnType<typeof vi.fn> };
  let mockRoleService: { getRoles: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockUserService = {
      getUsers: vi.fn().mockReturnValue(of([
        {
          id: "u1",
          username: "admin",
          email: "admin@test.com",
          full_name: "Admin User",
          is_active: true,
          is_superuser: true,
          roles: ["ROLE_SUPER_ADMIN"],
          permissions: ["USER_MANAGE"],
        },
      ])),
      createUser: vi.fn(),
    };
    mockRoleService = {
      getRoles: vi.fn().mockReturnValue(of([
        { id: "r1", code: "ROLE_ADMIN", name: "Administrator", is_system: true, permissions: [] },
      ])),
    };

    component = new UserManagementComponent(
      mockUserService as unknown as UserService,
      mockRoleService as unknown as RoleService,
      new FormBuilder()
    );
  });

  it("should initialize and load users", () => {
    component.ngOnInit();
    expect(component.users().length).toBe(1);
    expect(component.activeUserCount()).toBe(1);
    expect(component.superuserCount()).toBe(1);
    expect(component.loading()).toBe(false);
  });

  it("should filter users by search query", () => {
    component.ngOnInit();
    expect(component.filteredUsers().length).toBe(1);

    component.searchQuery.set("nonexistent");
    expect(component.filteredUsers().length).toBe(0);

    component.searchQuery.set("admin");
    expect(component.filteredUsers().length).toBe(1);
  });

  it("should manage modal state", () => {
    component.openModal();
    expect(component.isModalOpen()).toBe(true);

    component.closeModal();
    expect(component.isModalOpen()).toBe(false);
  });
});
