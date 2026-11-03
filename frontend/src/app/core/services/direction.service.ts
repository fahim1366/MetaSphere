import { Injectable, signal } from "@angular/core";

export type Locale = "en" | "fa";
export type Direction = "ltr" | "rtl";

@Injectable({
  providedIn: "root",
})
export class DirectionService {
  currentLocale = signal<Locale>("en");
  currentDirection = signal<Direction>("ltr");

  setLocale(locale: Locale): void {
    this.currentLocale.set(locale);
    const dir: Direction = locale === "fa" ? "rtl" : "ltr";
    this.currentDirection.set(dir);

    document.documentElement.setAttribute("dir", dir);
    document.documentElement.setAttribute("lang", locale);
  }

  toggleDirection(): void {
    const nextLocale: Locale = this.currentLocale() === "en" ? "fa" : "en";
    this.setLocale(nextLocale);
  }
}
