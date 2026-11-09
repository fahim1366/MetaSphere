import { Injector, runInInjectionContext } from "@angular/core";
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from "@angular/router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { authGuard } from "./auth.guard";
import { AuthService } from "../services/auth.service";

describe("authGuard", () => {
  let auth: {
    isAuthenticated: ReturnType<typeof vi.fn>;
    hasPermission: ReturnType<typeof vi.fn>;
  };
  let injector: Injector;
  const createUrlTree = vi.fn((commands: string[]) => ({ commands }) as unknown as UrlTree);

  beforeEach(() => {
    createUrlTree.mockClear();
    auth = { isAuthenticated: vi.fn(), hasPermission: vi.fn() };
    injector = Injector.create({
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: { createUrlTree } },
      ],
    });
  });

  function run(data: Record<string, unknown> = {}): boolean | UrlTree {
    const route = { data } as unknown as ActivatedRouteSnapshot;
    return runInInjectionContext(injector, () =>
      authGuard(route, {} as RouterStateSnapshot)
    ) as boolean | UrlTree;
  }

  it("redirects anonymous users to the login page", () => {
    auth.isAuthenticated.mockReturnValue(false);
    run();
    expect(createUrlTree).toHaveBeenCalledWith(["/login"]);
  });

  it("allows an authenticated user on a route without a permission requirement", () => {
    auth.isAuthenticated.mockReturnValue(true);
    expect(run()).toBe(true);
  });

  it("allows a user who holds the required permission", () => {
    auth.isAuthenticated.mockReturnValue(true);
    auth.hasPermission.mockImplementation((p: string) => p === "USER_MANAGE");
    expect(run({ permission: "USER_MANAGE" })).toBe(true);
  });

  it("sends a user without the required permission to the home page", () => {
    auth.isAuthenticated.mockReturnValue(true);
    auth.hasPermission.mockReturnValue(false);
    run({ permission: "AUDIT_READ" });
    expect(createUrlTree).toHaveBeenCalledWith(["/"]);
  });
});
