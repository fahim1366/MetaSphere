import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { CreateRolePayload, Role, RoleUser } from "../models/user.model";

export interface Permission {
  id: string;
  code: string;
  name: string;
  module: string;
  description: string | null;
}

@Injectable({
  providedIn: "root",
})
export class RoleService {
  private baseUrl = "http://localhost:8000/api/v1/roles";

  constructor(private http: HttpClient) {}

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(this.baseUrl);
  }

  getPermissions(): Observable<Permission[]> {
    return this.http.get<Permission[]>(`${this.baseUrl}/permissions`);
  }

  createRole(payload: CreateRolePayload): Observable<Role> {
    return this.http.post<Role>(this.baseUrl, payload);
  }

  getRoleUsers(roleId: string): Observable<RoleUser[]> {
    return this.http.get<RoleUser[]>(`${this.baseUrl}/${roleId}/users`);
  }
}
