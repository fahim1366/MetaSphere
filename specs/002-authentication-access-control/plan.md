# Implementation Plan: Authentication & Access Control

**Branch**: `002-authentication-access-control` | **Date**: 2026-11-03 | **Spec**: [specs/002-authentication-access-control/spec.md](spec.md)

**Input**: Feature specification from `specs/002-authentication-access-control/spec.md`

---

## Summary

Implement local user authentication, stateful session lifecycle management with instant revocation, fine-grained Role-Based Access Control (RBAC), hierarchical category and source-scoped permissions with parent-to-descendant inheritance, server-side authorization enforcement (deny-by-default), administrative user/role interfaces, and append-only security audit logging for the MetaSphere Enterprise Data Catalog.

All password storage uses **Argon2id** via `argon2-cffi`. Tokens are high-entropy (256-bit) cryptographically random strings whose SHA-256 digests are stored in PostgreSQL (`app_user_session`) and cached in Redis for fast verification and instant revocation across all user devices.

---

## Technical Context

**Language/Version**:
- Backend: Python 3.12 (pinned in `backend/.python-version` and `pyproject.toml`)
- Frontend: TypeScript strict mode / Node.js 22.22.3, npm 10.9.8

**Primary Dependencies**:
- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x (synchronous), Alembic, `argon2-cffi`, `redis-py`, HTTPX
- Frontend: Angular 22 Standalone Components, PrimeNG, PrimeIcons, Tailwind CSS 4, Vitest

**Storage & Broker**:
- Central PostgreSQL 16+ (schema `public`, tables `app_user`, `app_role`, `app_permission`, `app_user_role`, `app_role_permission`, `app_user_session`, `app_security_audit`)
- Redis 7+ (session cache & sliding-window brute-force rate limiter)

**Testing & Quality**:
- Backend: Pytest with SQLite in-memory / test fixtures, Ruff, Mypy strict mode
- Frontend: Vitest, Angular ESLint

**Target Platform**:
- On-premises air-gapped Linux containers & local Windows hybrid development

**Performance Targets**:
- Authentication verification overhead on requests: < 5ms
- Instant session revocation propagation: < 50ms
- Password hashing verification duration: 200–300ms (Argon2id memory-hard)
- 100% rejection of unauthorized API calls with HTTP 401/403

---

## Constitution Check

*GATE: All principles evaluated and verified.*

| Principle | Requirement Summary | Architectural Compliance | Status |
|---|---|---|:---:|
| **1. On-Premises & Dependencies** | No public internet, CDNs, or external auth providers. | Local username/password only. All hashing and token verification executes entirely locally in-process. | **PASS** |
| **2. Approved Stack & Boundaries** | FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis, Angular 22, PrimeNG, Tailwind 4. | Exact approved stack used. No unauthorized libraries or external dependencies. | **PASS** |
| **5. Security & Authorization** | Argon2id hashing, deny-by-default, no secrets in logs, multi-role RBAC, instant revocation, auditability. | Argon2id configured via `argon2-cffi`. Server-side dependency enforces permissions (deny-by-default). SHA-256 token hashing. Append-only security audit table. | **PASS** |
| **6. Explicit API Contracts** | Thin routers, Pydantic request/response schemas, generic error messages. | Explicit OpenAPI 3.1 contract (`auth-api.yaml`). Pydantic models with `SecretStr` for credentials. | **PASS** |
| **8. PostgreSQL Integrity** | Single schema `public`, Alembic migrations, UUID defaults, UTC timestamps. | All new auth entities defined in `public` with UUID primary keys and UTC timezone-aware timestamps. Migration `0002_auth_access_control.py`. | **PASS** |
| **9. Audit History** | Traceable events, audit logging for credential/governance actions. | Dedicated `app_security_audit` table logs logins, failures, lockouts, password updates, and role assignments without passwords. | **PASS** |
| **10. Accessible Angular UX** | Standalone Components, PrimeNG, RTL/LTR support, responsive forms. | Angular login view and user management table using PrimeNG and CSS logical properties. | **PASS** |
| **11. Mandatory Testing** | Unit tests, security regression tests, contract tests. | Pytest tests for Argon2id hashing, token verification, RBAC permissions, and session revocation. Vitest frontend tests for auth service and forms. | **PASS** |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-authentication-access-control/
├── spec.md              # Approved feature specification
├── checklists/
│   └── requirements.md  # Requirements quality checklist (100% PASS)
├── plan.md              # This technical implementation plan
├── research.md          # Argon2id, session lifecycle, and RBAC decisions
├── data-model.md        # Relational tables and Pydantic DTO models
├── quickstart.md        # End-to-end verification and curl scenarios
└── contracts/
    └── auth-api.yaml    # OpenAPI 3.1 specification for auth and user management
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 0002_auth_access_control.py   # Migration for users, roles, sessions, audit tables
├── app/
│   ├── api/
│   │   ├── deps.py                   # get_current_user, require_permissions dependencies
│   │   └── routes/
│   │       ├── auth.py               # /auth/login, /auth/logout, /auth/me, /auth/change-password
│   │       ├── users.py              # /users endpoints (list, create, update)
│   │       ├── roles.py              # /roles endpoints
│   │       └── audit.py              # /audit/security endpoints
│   ├── core/
│   │   ├── security.py               # Argon2id hasher, token generator, constant-time verify
│   │   └── rate_limit.py             # Redis sliding-window brute force protection
│   ├── models/
│   │   ├── user.py                   # SQLAlchemy models: AppUser, AppUserSession
│   │   ├── role.py                   # AppRole, AppPermission, AppUserRole, AppRolePermission
│   │   └── audit.py                  # AppSecurityAudit
│   ├── repositories/
│   │   ├── user_repository.py        # Persistence queries for users and sessions
│   │   └── audit_repository.py       # Persistence queries for audit logging
│   ├── schemas/
│   │   ├── auth.py                   # Pydantic auth schemas (LoginRequest, TokenResponse)
│   │   ├── user.py                   # UserRead, UserCreate, UserUpdate
│   │   └── role.py                   # RoleRead, PermissionRead
│   └── services/
│       ├── auth_service.py           # Login, session verification, revocation, password change
│       └── rbac_service.py           # Multi-role permission aggregation & hierarchy calculation
└── tests/
    ├── unit/
    │   ├── test_security.py          # Argon2id hashing and token entropy tests
    │   ├── test_auth_service.py      # Session management and lockout tests
    │   └── test_rbac.py              # Permission union and deny-by-default tests
    └── integration/
        ├── test_auth_api.py          # HTTP API tests for login, me, logout, 401, 403
        └── test_session_safety.py    # Revocation and concurrent lockout tests

frontend/
├── src/app/
│   ├── core/
│   │   ├── guards/
│   │   │   └── auth.guard.ts         # Angular route guard enforcing authenticated session
│   │   ├── interceptors/
│   │   │   └── auth.interceptor.ts   # Attaches Bearer token to API requests; handles 401
│   │   ├── models/
│   │   │   └── user.model.ts         # User, Role, Session, Permission interfaces
│   │   └── services/
│   │       └── auth.service.ts       # Login, logout, session Signal state, permission checks
│   └── features/
│       ├── auth/
│       │   └── login/                # Standalone Login form component
│       └── admin/
│           └── user-management/      # Standalone user & role management component
```

---

## Complexity Tracking

*No violations. Design strictly complies with all 14 Constitution principles.*
