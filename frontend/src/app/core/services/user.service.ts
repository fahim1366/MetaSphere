import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { User } from "../models/user.model";

export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role_codes: string[];
}

@Injectable({
  providedIn: "root",
})
export class UserService {
  private baseUrl = "http://localhost:8000/api/v1/users";

  constructor(private http: HttpClient) {}

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl);
  }

  createUser(payload: CreateUserPayload): Observable<User> {
    return this.http.post<User>(this.baseUrl, payload);
  }
}
