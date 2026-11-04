import { Routes } from "@angular/router";
import { ShellComponent } from "./layout/shell.component";
import { HealthDashboardComponent } from "./features/health-dashboard/health-dashboard.component";
import { LoginComponent } from "./features/auth/login/login.component";

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
    ],
  },
];
