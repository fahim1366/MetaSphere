import { HttpClient } from "@angular/common/http";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { AuthService } from "./auth.service";
import { TokenResponse } from "../models/user.model";

describe("AuthService", () => {
  let service: AuthService;
  let mockHttpClient: { post: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    localStorage.clear();
    mockHttpClient = {
      post: vi.fn(),
    };
    service = new AuthService(mockHttpClient as unknown as HttpClient);
  });

  it("should initialize unauthenticated by default", () => {
    expect(service.isAuthenticated()).toBe(false);
    expect(service.currentUser()).toBeNull();
    expect(service.token()).toBeNull();
  });

  it("should store token and user upon successful login", () => {
    const mockTokenRes: TokenResponse = {
      access_token: "test_token_123",
      token_type: "bearer",
      expires_at: "2026-11-04T12:00:00Z",
      user: {
        id: "11111111-1111-1111-1111-111111111111",
        username: "testuser",
        email: "test@example.com",
        full_name: "Test User",
        is_active: true,
        is_superuser: false,
        roles: ["ROLE_USER"],
        permissions: ["CATALOG_READ"],
      },
    };
    mockHttpClient.post.mockReturnValue(of(mockTokenRes));

    service.login({ username: "testuser", password: "Password123!" }).subscribe(() => {
      expect(service.isAuthenticated()).toBe(true);
      expect(service.currentUser()?.username).toBe("testuser");
      expect(service.hasPermission("CATALOG_READ")).toBe(true);
      expect(service.hasPermission("USER_MANAGE")).toBe(false);
      expect(service.hasRole("ROLE_USER")).toBe(true);
    });
  });

  it("should clear session and storage upon logout", () => {
    service.token.set("valid_token");
    service.currentUser.set({
      id: "uuid",
      username: "u",
      email: "u@e.com",
      full_name: null,
      is_active: true,
      is_superuser: false,
      roles: [],
      permissions: [],
    });
    mockHttpClient.post.mockReturnValue(of(undefined));

    service.logout().subscribe(() => {
      expect(service.isAuthenticated()).toBe(false);
      expect(service.token()).toBeNull();
      expect(service.currentUser()).toBeNull();
    });
  });

  describe("session restore", () => {
    const user = {
      id: "u1",
      username: "alice",
      email: "a@e.com",
      full_name: null,
      is_active: true,
      is_superuser: false,
      roles: [],
      permissions: [],
    };

    function seed(expiresAt: string | null): void {
      localStorage.setItem("metasphere_token", "tok");
      localStorage.setItem("metasphere_user", JSON.stringify(user));
      if (expiresAt) localStorage.setItem("metasphere_expires_at", expiresAt);
    }

    it("restores a stored session that has not expired", () => {
      seed(new Date(Date.now() + 3_600_000).toISOString());
      const restored = new AuthService(mockHttpClient as unknown as HttpClient);
      expect(restored.isAuthenticated()).toBe(true);
    });

    it("discards an expired stored session", () => {
      seed(new Date(Date.now() - 1_000).toISOString());
      const restored = new AuthService(mockHttpClient as unknown as HttpClient);
      expect(restored.isAuthenticated()).toBe(false);
      expect(localStorage.getItem("metasphere_token")).toBeNull();
    });

    it("discards a stored session with no recorded expiry", () => {
      seed(null);
      const restored = new AuthService(mockHttpClient as unknown as HttpClient);
      expect(restored.isAuthenticated()).toBe(false);
    });
  });
});
