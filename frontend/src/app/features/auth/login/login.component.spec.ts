import { FormBuilder } from "@angular/forms";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { of } from "rxjs";
import { LoginComponent } from "./login.component";
import { AuthService } from "../../../core/services/auth.service";
import { Router } from "@angular/router";

describe("LoginComponent", () => {
  let component: LoginComponent;
  let mockAuthService: { login: ReturnType<typeof vi.fn> };
  let mockRouter: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockAuthService = {
      login: vi.fn().mockReturnValue(of({})),
    };
    mockRouter = {
      navigate: vi.fn(),
    };
    component = new LoginComponent(
      new FormBuilder(),
      mockAuthService as unknown as AuthService,
      mockRouter as unknown as Router
    );
  });

  it("should create login form with required validators", () => {
    expect(component.loginForm).toBeTruthy();
    expect(component.loginForm.valid).toBe(false);

    component.loginForm.patchValue({ username: "alice", password: "Password123!" });
    expect(component.loginForm.valid).toBe(true);
  });

  it("should submit login credentials and navigate on success", () => {
    component.loginForm.patchValue({ username: "alice", password: "Password123!" });
    component.onSubmit();

    expect(mockAuthService.login).toHaveBeenCalledWith({
      username: "alice",
      password: "Password123!",
    });
    expect(mockRouter.navigate).toHaveBeenCalledWith(["/"]);
  });
});
