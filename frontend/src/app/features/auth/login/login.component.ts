import { Component, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from "@angular/forms";
import { Router } from "@angular/router";
import { AuthService } from "../../../core/services/auth.service";

@Component({
  selector: "app-login",
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="login-wrapper min-h-[70vh] flex items-center justify-center p-4">
      <div class="w-full max-w-md bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-blue-50 text-blue-600 mb-3">
            <i class="pi pi-lock text-xl" aria-hidden="true"></i>
          </div>
          <h2 class="text-2xl font-bold text-slate-800">Sign in to MetaSphere</h2>
          <p class="text-xs text-slate-500 mt-1">Enterprise Data Catalog & Metadata Governance</p>
        </div>

        <div *ngIf="errorMessage()" class="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
          {{ errorMessage() }}
        </div>

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
          <div class="mb-4">
            <label for="username" class="block text-xs font-semibold text-slate-700 mb-1">Username</label>
            <input
              id="username"
              type="text"
              formControlName="username"
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your username"
              autocomplete="username"
            />
          </div>

          <div class="mb-6">
            <label for="password" class="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <input
              id="password"
              type="password"
              formControlName="password"
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your password"
              autocomplete="current-password"
            />
          </div>

          <button
            type="submit"
            [disabled]="loginForm.invalid || loading()"
            class="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-lg shadow-sm transition-colors disabled:opacity-50"
          >
            <span *ngIf="!loading()">Sign in</span>
            <span *ngIf="loading()">Signing in...</span>
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
  `],
})
export class LoginComponent {
  loginForm: FormGroup;
  loading = signal(false);
  errorMessage = signal<string | null>(null);

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      username: ["", [Validators.required]],
      password: ["", [Validators.required]],
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) return;

    this.loading.set(true);
    this.errorMessage.set(null);

    this.authService.login(this.loginForm.value).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(["/"]);
      },
      error: (err: { error?: { detail?: string } }) => {
        this.loading.set(false);
        this.errorMessage.set(err.error?.detail || "Invalid username or password");
      },
    });
  }
}
