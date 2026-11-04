import { HttpClient } from "@angular/common/http";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { UserService } from "./user.service";

describe("UserService", () => {
  let service: UserService;
  let mockHttpClient: { get: ReturnType<typeof vi.fn>; post: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockHttpClient = {
      get: vi.fn(),
      post: vi.fn(),
    };
    service = new UserService(mockHttpClient as unknown as HttpClient);
  });

  it("should retrieve users from backend API", () => {
    const mockUsers = [
      {
        id: "1",
        username: "admin",
        email: "admin@example.com",
        full_name: "Admin",
        is_active: true,
        is_superuser: true,
        roles: ["ROLE_SUPER_ADMIN"],
        permissions: ["USER_MANAGE"],
      },
    ];
    mockHttpClient.get.mockReturnValue(of(mockUsers));

    service.getUsers().subscribe((data) => {
      expect(data.length).toBe(1);
      expect(data[0].username).toBe("admin");
    });
  });

  it("should create new user with payload", () => {
    const payload = {
      username: "newuser",
      email: "new@example.com",
      password: "Secret123Password!",
      role_codes: ["ROLE_USER"],
    };
    mockHttpClient.post.mockReturnValue(of({ ...payload, id: "2", is_active: true, is_superuser: false, roles: ["ROLE_USER"], permissions: [] }));

    service.createUser(payload).subscribe((res) => {
      expect(res.username).toBe("newuser");
      expect(mockHttpClient.post).toHaveBeenCalled();
    });
  });
});
