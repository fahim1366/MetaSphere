import { Component } from "@angular/core";
import { RouterOutlet } from "@angular/router";
import { DirectionService } from "../core/services/direction.service";

@Component({
  selector: "app-shell",
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: "./shell.component.html",
  styleUrls: ["./shell.component.scss"],
})
export class ShellComponent {
  constructor(public directionService: DirectionService) {}
}
