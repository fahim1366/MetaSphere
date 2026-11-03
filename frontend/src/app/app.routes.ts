import { Routes } from "@angular/router";
import { ShellComponent } from "./layout/shell.component";
import { HealthDashboardComponent } from "./features/health-dashboard/health-dashboard.component";

export const routes: Routes = [
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
