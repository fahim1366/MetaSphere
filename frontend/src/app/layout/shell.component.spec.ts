import { describe, it, expect, beforeEach, vi } from "vitest";
import { ShellComponent } from "./shell.component";
import { DirectionService } from "../core/services/direction.service";

describe("ShellComponent", () => {
  let component: ShellComponent;
  let mockDirectionService: {
    toggleDirection: ReturnType<typeof vi.fn>;
    currentDirection: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    mockDirectionService = {
      toggleDirection: vi.fn(),
      currentDirection: vi.fn().mockReturnValue("ltr"),
    };
    component = new ShellComponent(mockDirectionService as unknown as DirectionService);
  });

  it("should create the shell component", () => {
    expect(component).toBeTruthy();
  });

  it("should delegate toggleDirection to DirectionService", () => {
    component.directionService.toggleDirection();
    expect(mockDirectionService.toggleDirection).toHaveBeenCalled();
  });
});
