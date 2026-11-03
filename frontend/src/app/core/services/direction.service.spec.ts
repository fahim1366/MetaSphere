import { describe, it, expect, beforeEach } from "vitest";
import { DirectionService } from "./direction.service";

describe("DirectionService", () => {
  let service: DirectionService;

  beforeEach(() => {
    service = new DirectionService();
  });

  it("should initialize with default English and LTR", () => {
    expect(service.currentLocale()).toBe("en");
    expect(service.currentDirection()).toBe("ltr");
  });

  it("should switch to Persian and RTL and update DOM attributes", () => {
    service.setLocale("fa");
    expect(service.currentLocale()).toBe("fa");
    expect(service.currentDirection()).toBe("rtl");
    expect(document.documentElement.getAttribute("dir")).toBe("rtl");
    expect(document.documentElement.getAttribute("lang")).toBe("fa");
  });

  it("should toggle direction between LTR and RTL", () => {
    service.toggleDirection();
    expect(service.currentLocale()).toBe("fa");
    expect(service.currentDirection()).toBe("rtl");

    service.toggleDirection();
    expect(service.currentLocale()).toBe("en");
    expect(service.currentDirection()).toBe("ltr");
  });
});
