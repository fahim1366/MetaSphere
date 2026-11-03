import { Component, OnInit } from "@angular/core";
import { CommonModule } from "@angular/common";
import { HealthService } from "../../core/services/health.service";

@Component({
  selector: "app-health-dashboard",
  standalone: true,
  imports: [CommonModule],
  templateUrl: "./health-dashboard.component.html",
  styleUrls: ["./health-dashboard.component.scss"],
})
export class HealthDashboardComponent implements OnInit {
  constructor(public healthService: HealthService) {}

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.healthService.checkReadiness().subscribe();
  }

  getComponentKeys(components: Record<string, unknown> | undefined): string[] {
    return components ? Object.keys(components) : [];
  }
}
