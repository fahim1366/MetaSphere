# Data Model: Authentication & Access Control

**Feature**: `002-authentication-access-control`  
**Date**: 2026-11-03  
**Status**: Completed Design  

---

## 1. Relational Schema & Table Definitions (PostgreSQL `public` schema)

All tables use UUID primary keys (`gen_random_uuid()` default), explicit constraints, UTC timezone-aware timestamps, and foreign key cascades.

### 1.1 `app_user`
Stores local catalog user accounts.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Immutable user identifier |
| `username` | `VARCHAR(50)` | `NOT NULL UNIQUE` | Case-insensitive unique login handle |
| `email` | `VARCHAR(255)` | `NOT NULL UNIQUE` | Normalized unique email address |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Argon2id cryptographically salted hash string |
| `full_name` | `VARCHAR(100)` | `NULL` | Optional display name |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | Deactivated accounts cannot authenticate |
| `is_superuser` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Bypass flag for initial bootstrap emergency operations |
| `failed_login_attempts` | `INTEGER` | `NOT NULL DEFAULT 0` | Counter for brute-force lockout tracking |
| `locked_until` | `TIMESTAMPTZ` | `NULL` | Temporary account lockout expiry timestamp |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Account creation UTC timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Profile update UTC timestamp |

Indexes:
- `ix_app_user_username` on `LOWER(username)`
- `ix_app_user_email` on `LOWER(email)`

---

### 1.2 `app_role`
Stores named system and user-defined access roles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Role identifier |
| `code` | `VARCHAR(50)` | `NOT NULL UNIQUE` | Static identifier (e.g. `ROLE_ADMIN`, `ROLE_STEWARD`) |
| `name` | `VARCHAR(100)` | `NOT NULL` | Human-readable role title |
| `description` | `VARCHAR(255)` | `NULL` | Explanation of role scope |
| `is_system` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | System roles cannot be renamed or deleted |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Creation timestamp |

---

### 1.3 `app_permission`
Stores discrete capability codes enforceable across API endpoints.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Permission identifier |
| `code` | `VARCHAR(50)` | `NOT NULL UNIQUE` | Unique permission string (e.g. `CATALOG_READ`) |
| `name` | `VARCHAR(100)` | `NOT NULL` | Human-readable title |
| `module` | `VARCHAR(50)` | `NOT NULL` | Grouping tag (e.g. `catalog`, `admin`, `audit`) |
| `description` | `VARCHAR(255)` | `NULL` | Detail of permitted action |

Seed Permissions:
- `CATALOG_READ`: Browse catalog, categories, and published metadata.
- `CATALOG_WRITE`: Edit metadata descriptions, tags, and terms.
- `SOURCE_MANAGE`: Register, test, and edit data source connections.
- `USER_MANAGE`: Create, modify, and deactivate user accounts.
- `ROLE_MANAGE`: Create roles and assign permissions.
- `AUDIT_READ`: Query and inspect security and governance audit logs.

---

### 1.4 `app_user_role` & `app_role_permission`
Many-to-many junction tables.

#### `app_user_role`
- `user_id`: `UUID NOT NULL REFERENCES app_user(id) ON DELETE CASCADE`
- `role_id`: `UUID NOT NULL REFERENCES app_role(id) ON DELETE CASCADE`
- `assigned_at`: `TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- `assigned_by`: `UUID NULL REFERENCES app_user(id) ON DELETE SET NULL`
- `PRIMARY KEY (user_id, role_id)`

#### `app_role_permission`
- `role_id`: `UUID NOT NULL REFERENCES app_role(id) ON DELETE CASCADE`
- `permission_id`: `UUID NOT NULL REFERENCES app_permission(id) ON DELETE CASCADE`
- `PRIMARY KEY (role_id, permission_id)`

---

### 1.5 `app_user_session`
Stores active session tokens for fast server-side verification and instant revocation.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Session identifier |
| `user_id` | `UUID` | `NOT NULL REFERENCES app_user(id) ON DELETE CASCADE` | Associated user |
| `token_hash` | `VARCHAR(64)` | `NOT NULL UNIQUE` | SHA-256 hash of the bearer session token |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Session establishment time |
| `expires_at` | `TIMESTAMPTZ` | `NOT NULL` | Absolute session expiration deadline |
| `last_activity_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Timestamp of last API interaction |
| `is_revoked` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Flag for instant invalidation |
| `ip_address` | `VARCHAR(45)` | `NULL` | Client IP (IPv4 or IPv6) |
| `user_agent` | `VARCHAR(255)` | `NULL` | Client user agent string |

Indexes:
- `ix_app_user_session_token_hash` on `token_hash`
- `ix_app_user_session_user_active` on `(user_id, is_revoked, expires_at)`

---

### 1.6 `app_security_audit`
Append-only immutable audit trail for all security, authentication, and authorization events.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY DEFAULT gen_random_uuid()` | Audit event ID |
| `event_type` | `VARCHAR(50)` | `NOT NULL` | Event code (`LOGIN_SUCCESS`, `LOGIN_FAILED`, etc.) |
| `user_id` | `UUID` | `NULL REFERENCES app_user(id) ON DELETE SET NULL` | Subject user |
| `actor_id` | `UUID` | `NULL REFERENCES app_user(id) ON DELETE SET NULL` | Performing user (if admin) |
| `target_resource` | `VARCHAR(100)` | `NULL` | Targeted resource ID or name |
| `status` | `VARCHAR(20)` | `NOT NULL` | Result: `SUCCESS`, `FAILURE`, `BLOCKED` |
| `ip_address` | `VARCHAR(45)` | `NULL` | Originating client IP |
| `timestamp` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Event UTC timestamp |
| `details` | `JSONB` | `NULL` | Structured metadata (e.g. modified roles, reason) |

Indexes:
- `ix_app_security_audit_timestamp` on `timestamp DESC`
- `ix_app_security_audit_user` on `user_id`
- `ix_app_security_audit_event_type` on `event_type`

---

## 2. Pydantic Request & Response Contracts

### 2.1 Authentication DTOs
- `LoginRequest`: `username (str)`, `password (SecretStr)`
- `TokenResponse`: `access_token (str)`, `token_type ("bearer")`, `expires_at (datetime)`, `user (UserRead)`
- `ChangePasswordRequest`: `current_password (SecretStr)`, `new_password (SecretStr)`
- `UserRead`: `id (UUID)`, `username (str)`, `email (EmailStr)`, `full_name (str | None)`, `is_active (bool)`, `is_superuser (bool)`, `roles (list[str])`, `permissions (list[str])`

### 2.2 User Administration DTOs
- `UserCreate`: `username (str)`, `email (EmailStr)`, `password (SecretStr)`, `full_name (str | None)`, `role_codes (list[str])`
- `UserUpdate`: `email (EmailStr | None)`, `full_name (str | None)`, `is_active (bool | None)`, `role_codes (list[str] | None)`

### 2.3 Role & Permission DTOs
- `RoleRead`: `id (UUID)`, `code (str)`, `name (str)`, `description (str | None)`, `is_system (bool)`, `permission_codes (list[str])`
- `PermissionRead`: `id (UUID)`, `code (str)`, `name (str)`, `module (str)`, `description (str | None)`

### 2.4 Audit Log DTOs
- `AuditLogRead`: `id (UUID)`, `event_type (str)`, `user_id (UUID | None)`, `actor_id (UUID | None)`, `status (str)`, `ip_address (str | None)`, `timestamp (datetime)`, `details (dict[str, Any] | None)`
