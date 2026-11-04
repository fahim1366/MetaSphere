import { describe, it, expect, beforeEach, vi } from "vitest";
import { ShellComponent } from "./shell.component";
import { DirectionService } from "../core/services/direction.service";
import { AuthService } from "../core/services/auth.service";
import { Router } from "@angular/router";
import { of } from "rxjs";

describe("ShellComponent", () => {
  let component: ShellComponent;
  let mockDirectionService: {
    toggleDirection: ReturnType<typeof vi.fn>;
    currentDirection: ReturnType<typeof vi.fn>;
  };
  let mockAuthService: {
    logout: ReturnType<typeof vi.fn>;
    isAuthenticated: ReturnType<typeof vi.fn>;
    currentUser: ReturnType<typeof vi.fn>;
    hasPermission: ReturnType<typeof vi.fn>;
  };
  let mockRouter: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockDirectionService = {
      toggleDirection: vi.fn(),
      currentDirection: vi.fn().mockReturnValue("ltr"),
    };
    mockAuthService = {
      logout: vi.fn().mockReturnValue(of(undefined)),
      isAuthenticated: vi.fn().mockReturnValue(true),
      currentUser: vi.fn().mockReturnValue({ username: "alice", roles: ["ROLE_ADMIN"] }),
      hasPermission: vi.fn().mockReturnValue(true),
    };
    mockRouter = {
      navigate: vi.fn(),
    };

    component = new ShellComponent(
      mockDirectionService as unknown as DirectionService,
      mockAuthService as unknown as AuthService,
      mockRouter as unknown as Router
    );
  });

  it("should create the shell component", () => {
    expect(component).toBeTruthy();
  });

  it("should delegate toggleDirection to DirectionService", () => {
    component.directionService.toggleDirection();
    expect(mockDirectionService.toggleDirection).toHaveBeenCalled();
  });

  it("should trigger logout through AuthService", () => {
    component.logout();
    expect(mockAuthService.logout).toHaveBeenCalled();
  });
});
