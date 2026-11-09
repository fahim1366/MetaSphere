import { HttpErrorResponse, HttpInterceptorFn } from "@angular/common/http";
import { inject } from "@angular/core";
import { Router } from "@angular/router";
import { catchError, throwError } from "rxjs";
import { API_BASE } from "../api.config";
import { AuthService } from "../services/auth.service";

const AUTH_ENDPOINTS = [`${API_BASE}/auth/login`, `${API_BASE}/auth/logout`];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const isApiCall = req.url.startsWith(API_BASE);
  const token = authService.token();
  const outgoing =
    isApiCall && token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(outgoing).pipe(
    catchError((error: unknown) => {
      const isAuthEndpoint = AUTH_ENDPOINTS.some((url) => req.url.startsWith(url));
      if (
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        isApiCall &&
        !isAuthEndpoint &&
        authService.token() !== null
      ) {
        // Session expired or was revoked server-side: drop it and send the user to login.
        authService.clearSession();
        void router.navigate(["/login"]);
      }
      return throwError(() => error);
    })
  );
};
