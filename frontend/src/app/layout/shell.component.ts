import { Component } from "@angular/core";
import { CommonModule } from "@angular/common";
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";
import { DirectionService } from "../core/services/direction.service";
import { AuthService } from "../core/services/auth.service";

@Component({
  selector: "app-shell",
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: "./shell.component.html",
  styleUrls: ["./shell.component.scss"],
})
export class ShellComponent {
  constructor(
    public directionService: DirectionService,
    public authService: AuthService,
    private router: Router
  ) {}

  logout(): void {
    this.authService.logout().subscribe({
      next: () => this.router.navigate(["/login"]),
      error: () => this.router.navigate(["/login"]),
    });
  }
}
