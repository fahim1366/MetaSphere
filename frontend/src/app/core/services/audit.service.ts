import { Injectable } from "@angular/core";
import { API_BASE } from "../api.config";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Observable } from "rxjs";

export interface SecurityAuditLog {
  id: string;
  event_type: string;
  user_id: string | null;
  actor_id: string | null;
  target_resource: string | null;
  status: string;
  ip_address: string | null;
  timestamp: string;
  details: Record<string, unknown> | null;
}

@Injectable({
  providedIn: "root",
})
export class AuditService {
  private baseUrl = `${API_BASE}/audit/security`;

  constructor(private http: HttpClient) {}

  getAuditLogs(limit = 50, offset = 0): Observable<SecurityAuditLog[]> {
    const params = new HttpParams().set("limit", limit.toString()).set("offset", offset.toString());
    return this.http.get<SecurityAuditLog[]>(this.baseUrl, { params });
  }
}
