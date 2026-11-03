import { describe, it, expect, beforeEach } from "vitest";
import { AppComponent } from "./app.component";

describe("AppComponent", () => {
  let component: AppComponent;

  beforeEach(() => {
    component = new AppComponent();
  });

  it("should create the app and initialize default title", () => {
    expect(component).toBeTruthy();
    expect(component.title()).toBe("MetaSphere Enterprise Data Catalog");
  });
});
