import { inject } from "@angular/core";
import { CanActivateFn, Router } from "@angular/router";
import { AuthService } from "../services/auth.service";

/**
 * Requires an authenticated session. If the route declares `data: { permission: "CODE" }`
 * the user must also hold that permission, otherwise they are sent to the home page.
 * (The backend remains the authority; this only avoids showing screens that would fail.)
 */
export const authGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(["/login"]);
  }

  const required = route.data?.["permission"] as string | undefined;
  if (required && !authService.hasPermission(required)) {
    return router.createUrlTree(["/"]);
  }

  return true;
};
