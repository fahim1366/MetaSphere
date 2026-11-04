import { Injectable, computed, signal } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable, tap } from "rxjs";
import { LoginPayload, TokenResponse, User } from "../models/user.model";

@Injectable({
  providedIn: "root",
})
export class AuthService {
  private baseUrl = "http://localhost:8000/api/v1/auth";

  currentUser = signal<User | null>(null);
  token = signal<string | null>(null);
  isAuthenticated = computed(() => this.currentUser() !== null && this.token() !== null);

  constructor(private http: HttpClient) {
    const savedToken = localStorage.getItem("metasphere_token");
    const savedUser = localStorage.getItem("metasphere_user");
    if (savedToken && savedUser) {
      try {
        this.token.set(savedToken);
        this.currentUser.set(JSON.parse(savedUser));
      } catch {
        this.clearSession();
      }
    }
  }

  login(payload: LoginPayload): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.baseUrl}/login`, payload).pipe(
      tap((res) => {
        this.token.set(res.access_token);
        this.currentUser.set(res.user);
        localStorage.setItem("metasphere_token", res.access_token);
        localStorage.setItem("metasphere_user", JSON.stringify(res.user));
      })
    );
  }

  logout(): Observable<void> {
    const currentToken = this.token();
    this.clearSession();
    return this.http.post<void>(`${this.baseUrl}/logout`, {}, {
      headers: currentToken ? { Authorization: `Bearer ${currentToken}` } : {},
    });
  }

  clearSession(): void {
    this.token.set(null);
    this.currentUser.set(null);
    localStorage.removeItem("metasphere_token");
    localStorage.removeItem("metasphere_user");
  }

  hasPermission(permission: string): boolean {
    const user = this.currentUser();
    if (!user) return false;
    if (user.is_superuser) return true;
    return user.permissions.includes(permission);
  }

  hasRole(roleCode: string): boolean {
    const user = this.currentUser();
    if (!user) return false;
    if (user.is_superuser) return true;
    return user.roles.includes(roleCode);
  }
}
