# Tasks: Authentication & Access Control

**Branch**: `002-authentication-access-control`  
**Spec**: [specs/002-authentication-access-control/spec.md](spec.md)  
**Plan**: [specs/002-authentication-access-control/plan.md](plan.md)  
**Data Model**: [specs/002-authentication-access-control/data-model.md](data-model.md)  
**Research**: [specs/002-authentication-access-control/research.md](research.md)  
**Quickstart**: [specs/002-authentication-access-control/quickstart.md](quickstart.md)  
**Contracts**: [`contracts/auth-api.yaml`](contracts/auth-api.yaml)  

---

## Task Format & Conventions

- Each task begins with a Markdown checkbox and a sequential Task ID (`T001`–`T035`).
- `[P]` means the task can run in parallel after all listed dependencies are complete and does not modify files concurrently with another task.
- `[US1]`–`[US5]` maps the task to its parent User Story.
- Field constraints and types are quoted verbatim from `data-model.md`.
- Tests are mandatory deliverables. Unit tests must not require Docker; integration tests run against PostgreSQL and Redis.

---

## Phase 1: Setup — Toolchain & Dependency Manifests

**Purpose**: Add Argon2id security libraries and dependency locks for authentication.

- [X] T001 [P] Add `argon2-cffi>=23.1.0` to backend dependencies in `backend/requirements.in` and re-compile `backend/requirements.lock`.
- [X] T002 [P] Configure session security settings in `backend/app/core/config.py` (SESSION_EXPIRE_MINUTES, BCRYPT/ARGON2 parameters).

---

## Phase 2: Foundational — Persistence Models, Migrations & Core Security Engine

**Purpose**: Core database tables, security hashing, session storage, and audit logging infrastructure required by all user stories.

- [X] T003 [P] Implement SQLAlchemy user and session models (`AppUser`, `AppUserSession`) in `backend/app/models/user.py`. Quote constraints: `username (VARCHAR(50), NOT NULL, UNIQUE)`, `email (VARCHAR(255), NOT NULL, UNIQUE)`, `password_hash (VARCHAR(255), NOT NULL)`, `is_active (BOOLEAN, NOT NULL, DEFAULT TRUE)`.
- [X] T004 [P] Implement SQLAlchemy role and permission models (`AppRole`, `AppPermission`, `AppUserRole`, `AppRolePermission`) in `backend/app/models/role.py`. Quote constraints: `code (VARCHAR(50), NOT NULL, UNIQUE)`, `is_system (BOOLEAN, NOT NULL, DEFAULT FALSE)`.
- [X] T005 [P] Implement SQLAlchemy audit model (`AppSecurityAudit`) in `backend/app/models/audit.py`. Quote constraints: `event_type (VARCHAR(50), NOT NULL)`, `status (VARCHAR(20), NOT NULL)`.
- [X] T006 Create Alembic migration revision for authentication, RBAC, session, and audit schema in `backend/alembic/versions/0002_auth_access_control.py`.
- [X] T007 [P] Implement Argon2id password hashing and constant-time dummy verification in `backend/app/core/security.py`.
- [X] T008 [P] Implement high-entropy (256-bit) session token generation and SHA-256 token hashing in `backend/app/core/security.py`.
- [X] T009 [P] Implement security audit logging service in `backend/app/services/audit_service.py` to record events without leaking passwords.
- [X] T010 Implement database user and session repository methods in `backend/app/repositories/user_repository.py`.

---

## Phase 3: User Story 1 — Local User Authentication & Session Management (P1)

**Goal**: Local username/password login, constant-time verification, session creation, logout invalidation, and rate limiting.

- [X] T011 [P] [US1] Implement unit tests for Argon2id hashing, token entropy, and constant-time dummy verification in `backend/tests/unit/test_security.py`.
- [X] T012 [P] [US1] Implement Pydantic authentication DTOs (`LoginRequest`, `TokenResponse`, `UserRead`) in `backend/app/schemas/auth.py`.
- [X] T013 [US1] Implement authentication service with login, session creation, and logout in `backend/app/services/auth_service.py`.
- [X] T014 [US1] Implement Redis-backed sliding-window rate limiter for brute-force protection in `backend/app/core/rate_limit.py`.
- [X] T015 [US1] Implement HTTP route handlers for `POST /api/v1/auth/login` and `POST /api/v1/auth/logout` in `backend/app/api/routes/auth.py`.
- [X] T016 [US1] Implement FastAPI dependency `get_current_user` in `backend/app/api/deps.py` validating active session tokens.
- [X] T017 [US1] Implement `GET /api/v1/auth/me` returning current authenticated user profile in `backend/app/api/routes/auth.py`.
- [X] T018 [P] [US1] Implement integration tests for login, invalid credentials (generic 401), and logout in `backend/tests/integration/test_auth_api.py`.

---

## Phase 4: User Story 2 — Role-Based Access Control (RBAC) & Server Enforcement (P1)

**Goal**: Server-enforced permissions on protected routes (deny by default), multi-role permission aggregation.

- [X] T019 [P] [US2] Implement unit tests for multi-role permission calculation and deny-by-default behavior in `backend/tests/unit/test_rbac.py`.
- [X] T020 [US2] Implement RBAC service calculating union of permissions across assigned roles in `backend/app/services/rbac_service.py`.
- [X] T021 [US2] Implement FastAPI authorization dependency `require_permissions(*permission_codes)` in `backend/app/api/deps.py`.
- [X] T022 [US2] Seed system roles (`ROLE_SUPER_ADMIN`, `ROLE_ADMIN`, `ROLE_USER`) and default permissions in Alembic migration or bootstrap script.
- [X] T023 [P] [US2] Implement integration tests verifying HTTP 403 Forbidden on permission lack in `backend/tests/integration/test_auth_api.py`.

---

## Phase 5: User Story 3 — Hierarchical Category & Source Scoped Access Control (P2)

**Goal**: Automatic inheritance of parent category permissions to descendant categories and data sources.

- [X] T024 [P] [US3] Implement category scope models and recursive ancestry query in `backend/app/models/scope.py` and `backend/app/repositories/scope_repository.py`.
- [X] T025 [US3] Implement category hierarchy permission inheritance calculation in `backend/app/services/rbac_service.py`.
- [X] T026 [P] [US3] Implement unit tests verifying inherited permissions on descendant categories in `backend/tests/unit/test_rbac.py`.

---

## Phase 6: User Story 4 — User & Role Administration Interface (P2)

**Goal**: Admin API endpoints and Angular UI for managing users, roles, and viewing security audit logs.

- [X] T027 [P] [US4] Implement user management routes `GET /api/v1/users` and `POST /api/v1/users` (protected by `USER_MANAGE`) in `backend/app/api/routes/users.py`.
- [X] T028 [P] [US4] Implement role listing route `GET /api/v1/roles` (protected by `ROLE_MANAGE`) in `backend/app/api/routes/roles.py`.
- [X] T029 [P] [US4] Implement security audit query route `GET /api/v1/audit/security` (protected by `AUDIT_READ`) in `backend/app/api/routes/audit.py`.
- [X] T030 [P] [US4] Implement Angular authentication service, models, and HTTP interceptor in `frontend/src/app/core/services/auth.service.ts` and `frontend/src/app/core/interceptors/auth.interceptor.ts`.
- [X] T031 [US4] Implement standalone Login component with accessible PrimeNG form and RTL/LTR support in `frontend/src/app/features/auth/login/login.component.ts`.
- [X] T032 [P] [US4] Implement Vitest tests for Angular auth service and Login component in `frontend/src/app/core/services/auth.service.spec.ts` and `frontend/src/app/features/auth/login/login.component.spec.ts`.

---

## Phase 7: User Story 5 — Account Security & Session Revocation (P3)

**Goal**: Password change with instant invalidation of all active user sessions; administrative session revocation.

- [X] T033 [US5] Implement `POST /api/v1/auth/change-password` with automatic all-session invalidation in `backend/app/api/routes/auth.py`.
- [X] T034 [P] [US5] Implement integration test verifying instant token rejection after password change in `backend/tests/integration/test_session_safety.py`.

---

## Phase 8: Polish & Cross-Cutting Verification

**Purpose**: Execute automated verification gates, run end-to-end curl scenarios, and audit scope boundaries.

- [X] T035 Execute full automated verification script (`scripts/verify.ps1`) and confirm 100% test pass with zero lint or typing errors.

---

## Dependencies & Execution Order

```text
Phase 1: T001, T002 (Parallel setup)
  ↓
Phase 2: T003–T010 (Foundational models, migration, hashing engine, audit)
  ↓
Phase 3 (US1 - Auth & Sessions): T011–T018
  ↓
Phase 4 (US2 - RBAC & Permissions): T019–T023
  ↓
Phase 5 (US3 - Hierarchical Scopes): T024–T026
  ↓
Phase 6 (US4 - Admin API & UI): T027–T032
  ↓
Phase 7 (US5 - Session Revocation): T033–T034
  ↓
Phase 8: T035 (Full Quality Gate Verification)
```
