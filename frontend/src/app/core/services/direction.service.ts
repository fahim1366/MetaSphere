import { Injectable, signal } from "@angular/core";

export type Locale = "en" | "fa";
export type Direction = "ltr" | "rtl";

@Injectable({
  providedIn: "root",
})
export class DirectionService {
  currentLocale = signal<Locale>("fa");
  currentDirection = signal<Direction>("rtl");

  constructor() {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("dir", "rtl");
      document.documentElement.setAttribute("lang", "fa");
    }
  }

  setLocale(locale: Locale): void {
    this.currentLocale.set(locale);
    const dir: Direction = locale === "fa" ? "rtl" : "ltr";
    this.currentDirection.set(dir);

    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("dir", dir);
      document.documentElement.setAttribute("lang", locale);
    }
  }

  toggleDirection(): void {
    const nextLocale: Locale = this.currentLocale() === "fa" ? "en" : "fa";
    this.setLocale(nextLocale);
  }
}
