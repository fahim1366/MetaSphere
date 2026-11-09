import { Routes } from "@angular/router";
import { ShellComponent } from "./layout/shell.component";
import { HealthDashboardComponent } from "./features/health-dashboard/health-dashboard.component";
import { LoginComponent } from "./features/auth/login/login.component";
import { UserManagementComponent } from "./features/admin/users/user-management.component";
import { RoleManagementComponent } from "./features/admin/roles/role-management.component";
import { AuditLogComponent } from "./features/admin/audit/audit-log.component";
import { authGuard } from "./core/guards/auth.guard";

export const routes: Routes = [
  {
    path: "login",
    component: LoginComponent,
  },
  {
    path: "",
    component: ShellComponent,
    children: [
      {
        path: "",
        component: HealthDashboardComponent,
      },
      {
        path: "admin/users",
        component: UserManagementComponent,
        canActivate: [authGuard],
        data: { permission: "USER_MANAGE" },
      },
      {
        path: "admin/roles",
        component: RoleManagementComponent,
        canActivate: [authGuard],
        data: { permission: "ROLE_MANAGE" },
      },
      {
        path: "admin/audit",
        component: AuditLogComponent,
        canActivate: [authGuard],
        data: { permission: "AUDIT_READ" },
      },
    ],
  },
  {
    path: "**",
    redirectTo: "",
  },
];
