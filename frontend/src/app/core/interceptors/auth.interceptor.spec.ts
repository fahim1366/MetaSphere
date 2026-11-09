import { HttpErrorResponse, HttpEvent, HttpRequest, HttpResponse } from "@angular/common/http";
import { Injector, runInInjectionContext } from "@angular/core";
import { Router } from "@angular/router";
import { Observable, of, throwError } from "rxjs";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { authInterceptor } from "./auth.interceptor";
import { AuthService } from "../services/auth.service";

describe("authInterceptor", () => {
  let auth: { token: ReturnType<typeof vi.fn>; clearSession: ReturnType<typeof vi.fn> };
  let router: { navigate: ReturnType<typeof vi.fn> };
  let injector: Injector;

  beforeEach(() => {
    auth = { token: vi.fn().mockReturnValue("tok_123"), clearSession: vi.fn() };
    router = { navigate: vi.fn() };
    injector = Injector.create({
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: router },
      ],
    });
  });

  function run(
    req: HttpRequest<unknown>,
    next: (r: HttpRequest<unknown>) => Observable<HttpEvent<unknown>>
  ): Observable<HttpEvent<unknown>> {
    return runInInjectionContext(injector, () => authInterceptor(req, next));
  }

  it("adds the bearer token to API requests", () => {
    const next = vi.fn().mockReturnValue(of(new HttpResponse({ status: 200 })));
    run(new HttpRequest("GET", "/api/v1/users"), next).subscribe();
    expect(next.mock.calls[0][0].headers.get("Authorization")).toBe("Bearer tok_123");
  });

  it("does not leak the token to non-API requests", () => {
    const next = vi.fn().mockReturnValue(of(new HttpResponse({ status: 200 })));
    run(new HttpRequest("GET", "https://example.org/data"), next).subscribe();
    expect(next.mock.calls[0][0].headers.has("Authorization")).toBe(false);
  });

  it("clears the session and redirects on a 401 from the API", () => {
    const next = vi
      .fn()
      .mockReturnValue(throwError(() => new HttpErrorResponse({ status: 401 })));
    run(new HttpRequest("GET", "/api/v1/users"), next).subscribe({ error: () => undefined });
    expect(auth.clearSession).toHaveBeenCalledTimes(1);
    expect(router.navigate).toHaveBeenCalledWith(["/login"]);
  });

  it("does not treat a failed login (401) as an expired session", () => {
    const next = vi
      .fn()
      .mockReturnValue(throwError(() => new HttpErrorResponse({ status: 401 })));
    run(new HttpRequest("POST", "/api/v1/auth/login", {}), next).subscribe({
      error: () => undefined,
    });
    expect(auth.clearSession).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it("ignores 403 responses", () => {
    const next = vi
      .fn()
      .mockReturnValue(throwError(() => new HttpErrorResponse({ status: 403 })));
    run(new HttpRequest("GET", "/api/v1/users"), next).subscribe({ error: () => undefined });
    expect(auth.clearSession).not.toHaveBeenCalled();
  });
});
