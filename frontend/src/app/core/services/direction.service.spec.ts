import { describe, it, expect, beforeEach } from "vitest";
import { DirectionService } from "./direction.service";

describe("DirectionService", () => {
  let service: DirectionService;

  beforeEach(() => {
    service = new DirectionService();
  });

  it("should initialize with default Persian and RTL", () => {
    expect(service.currentLocale()).toBe("fa");
    expect(service.currentDirection()).toBe("rtl");
  });

  it("should switch to English and LTR and update DOM attributes", () => {
    service.setLocale("en");
    expect(service.currentLocale()).toBe("en");
    expect(service.currentDirection()).toBe("ltr");
    expect(document.documentElement.getAttribute("dir")).toBe("ltr");
    expect(document.documentElement.getAttribute("lang")).toBe("en");
  });

  it("should toggle direction between RTL and LTR", () => {
    service.toggleDirection();
    expect(service.currentLocale()).toBe("en");
    expect(service.currentDirection()).toBe("ltr");

    service.toggleDirection();
    expect(service.currentLocale()).toBe("fa");
    expect(service.currentDirection()).toBe("rtl");
  });
});
