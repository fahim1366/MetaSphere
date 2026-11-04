export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  roles: string[];
  permissions: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface Role {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
  permissions: string[];
  assigned_user_count?: number;
}

export interface RoleUser {
  id: string;
  username: string;
  full_name: string | null;
  email: string;
  is_active: boolean;
}

export interface CreateRolePayload {
  code: string;
  name: string;
  description?: string;
  permission_codes: string[];
}
