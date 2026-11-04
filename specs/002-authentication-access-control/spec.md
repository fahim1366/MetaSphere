# Feature Specification: Authentication & Access Control

**Feature Branch**: `002-authentication-access-control`

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "Define and implement the Authentication & Access Control feature for the MetaSphere Enterprise Data Catalog. Establish local user authentication with Argon2id password hashing, secure session management with revocation, multi-role RBAC, scoped permissions across categories and data sources with parent-to-descendant inheritance, server-side authorization enforcement (deny-by-default), and administrative security audit logging."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Local User Authentication & Session Management (Priority: P1)

As a catalog user, I want to authenticate locally using my username and password and receive a secure authenticated session, so that I can securely access the catalog while protecting my account against brute-force attacks and enumeration.

**Why this priority**: Authentication is the security perimeter for the entire catalog; without verified identity, no protected catalog data, metadata, or administrative functions can be exposed safely.

**Independent Test**: Can be tested independently by creating a local user account, attempting login with valid credentials (expecting successful session creation), attempting login with invalid credentials (expecting generic rejection without disclosing whether username exists), and exercising session logout and expiration.

**Acceptance Scenarios**:

1. **Given** an active local user with a valid username and password, **When** they submit valid credentials to the login interface, **Then** the system establishes an authenticated session, returns user identity information, and records an authentication audit event.
2. **Given** an unauthenticated request with invalid credentials or a non-existent username, **When** the login endpoint processes the request, **Then** it returns an identical generic error message ("Invalid username or password") in constant-time response behavior, preventing account enumeration.
3. **Given** repeated failed login attempts from a client, **When** the failure threshold is exceeded, **Then** the system applies progressive rate limiting or temporary lockout and records a security audit warning.
4. **Given** an authenticated user session, **When** the user logs out, **Then** the session is immediately invalidated on the server and cannot be reused for subsequent API calls.

---

### User Story 2 - Role-Based Access Control (RBAC) & Server-Enforced Permissions (Priority: P1)

As a security administrator, I want to assign one or more roles with explicit permissions to users, so that access to catalog metadata and administrative actions is strictly controlled and enforced by the server on every protected request.

**Why this priority**: Non-negotiable under Constitution Principle 5. The system must deny by default and verify effective permissions on every operation regardless of client UI state.

**Independent Test**: Can be tested independently by defining roles with distinct permission sets, assigning multiple roles to a test user, and verifying that the user can execute operations permitted by any assigned role while being denied with HTTP 403 for unauthorized operations.

**Acceptance Scenarios**:

1. **Given** a user assigned multiple roles (e.g. `DATA_STEWARD` and `AUDITOR`), **When** the user accesses protected operations, **Then** the system calculates the union of permissions from all assigned roles and permits operations matching any assigned permission.
2. **Given** a user lacking a required permission for an endpoint, **When** they issue a request, **Then** the server denies the request with an HTTP 403 Forbidden status, regardless of UI controls or URL tampering.
3. **Given** a request missing authentication, **When** any protected endpoint is called, **Then** the server denies the request with an HTTP 401 Unauthorized status.

---

### User Story 3 - Hierarchical Category & Source Scoped Access Control (Priority: P2)

As a catalog governor, I want to grant users and roles permissions scoped to specific categories or data sources with automatic inheritance from parent categories to descendant categories, so that access governance reflects organizational domain hierarchies.

**Why this priority**: Enterprise metadata catalogs organize thousands of databases into hierarchical business domains; manual access assignment at every level is error-prone and unsustainable.

**Independent Test**: Can be tested independently by creating a parent category with child subcategories and associated data sources, granting read permission on the parent category, and verifying that the user automatically inherits access to all child categories and sources within that hierarchy.

**Acceptance Scenarios**:

1. **Given** a user granted read access on category `Finance`, **When** the user queries metadata under `Finance -> Treasury` (a child category), **Then** the system permits access via inherited category scope.
2. **Given** access explicitly restricted on a descendant category or data source, **When** effective permissions are calculated, **Then** the backend enforces the documented hierarchy precedence rules.
3. **Given** a direct source permission grant without category membership, **When** the user accesses that specific source, **Then** access is permitted for that source only without granting category-wide visibility.

---

### User Story 4 - User & Role Administration Interface (Priority: P2)

As a system administrator, I want an administrative interface to create users, assign roles, inspect active permissions, and view security audit logs, so that user lifecycle and access control can be managed reliably.

**Why this priority**: Essential operational capability for user onboarding, role provisioning, and compliance verification.

**Independent Test**: Can be tested independently by navigating to the administration panel as an authorized administrator, creating a new user, modifying role assignments, and observing corresponding audit log entries.

**Acceptance Scenarios**:

1. **Given** an authenticated administrator with `USER_MANAGE` permission, **When** they create a new user account, **Then** the user is created with a temporary password adhering to complexity requirements, and an audit event is logged.
2. **Given** a user without administrative permissions, **When** they attempt to access user management endpoints or screens, **Then** access is rejected with HTTP 403 and the attempt is audited.

---

### User Story 5 - Account Security, Password Lifecycle & Session Revocation (Priority: P3)

As a security auditor or user, I want password change workflows to immediately invalidate all existing sessions and allow administrators to revoke active user sessions on demand, so that compromised credentials can be neutralized immediately.

**Why this priority**: Required by Constitution Principle 5 for incident containment and credential lifecycle safety.

**Independent Test**: Can be tested independently by establishing multiple active sessions for a user, changing the user's password in one session, and verifying that all other sessions are immediately rejected on their next API call.

**Acceptance Scenarios**:

1. **Given** multiple active sessions for a user, **When** the user successfully updates their password, **Then** all existing sessions for that user are revoked.
2. **Given** an authorized administrator, **When** they invoke session revocation for a specific user, **Then** all active tokens/sessions for that user are terminated immediately.

---

### Edge Cases

- **Concurrent Session Lockout**: When an account reaches maximum failed login attempts simultaneously across multiple clients, lockout must be applied atomically to prevent race-condition bypass.
- **Account Deactivation Mid-Session**: If an administrator deactivates or locks an account, any active sessions must be rejected on their very next request without waiting for token expiration.
- **Role Revocation Mid-Session**: If a role or permission is removed from an active user, subsequent requests must immediately reflect the reduced permissions.
- **Inherited vs. Direct Permission Conflicts**: When a user possesses both an inherited category grant and a direct source restriction, explicit precedence rules must resolve the conflict deterministically.
- **Clock Skew on Token Expiry**: Token validation must handle minor server clock drift (e.g. 5-second grace window) while strictly refusing expired tokens.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate users using local username and password credentials. External AD/LDAP/SSO integrations are strictly out of scope.
- **FR-002**: Password storage MUST use Argon2id hashing with secure, approved parameter bounds (time cost, memory cost, parallelism). Plaintext passwords and reversible encryption are strictly prohibited.
- **FR-003**: System MUST enforce password complexity: minimum 12 characters, requiring uppercase, lowercase, numbers, and symbols, and rejecting common compromised passwords.
- **FR-004**: System MUST implement secure session management with configurable session timeout, sliding activity expiration, and explicit logout invalidation.
- **FR-005**: Authentication failure responses MUST NOT reveal whether the username exists or whether the password was incorrect (constant-time response with generic error).
- **FR-006**: System MUST enforce progressive rate limiting on authentication endpoints to mitigate automated brute-force attacks.
- **FR-007**: Role-Based Access Control (RBAC) MUST support users with multiple assigned roles, calculating effective permissions as the union of all assigned roles.
- **FR-008**: System MUST implement explicit, fine-grained permission codes (e.g. `CATALOG_READ`, `CATALOG_WRITE`, `SOURCE_MANAGE`, `USER_MANAGE`, `AUDIT_READ`).
- **FR-009**: Backend MUST enforce effective permissions on every protected HTTP route; missing or ambiguous permissions MUST result in default denial (HTTP 403). UI control visibility MUST NOT be treated as a security boundary.
- **FR-010**: System MUST support category-scoped access control where parent category grants automatically inherit to all descendant categories and child data sources.
- **FR-011**: System MUST support direct source-scoped access grants for specific data sources without requiring full category access.
- **FR-012**: System MUST provide an administrative user management API and UI view for creating users, updating profiles, and assigning roles.
- **FR-013**: System MUST provide an administrative role management API and UI view for inspecting and modifying role permission assignments.
- **FR-014**: Changing an account password MUST immediately revoke and invalidate all active sessions for that user account.
- **FR-015**: Administrators MUST be able to immediately revoke all active sessions for any selected user account.
- **FR-016**: System MUST log security audit records for: login attempts (success/failure), logouts, password changes, account lockouts, user creation/modification, and role assignment modifications. Audit logs MUST NEVER contain passwords or raw credentials.
- **FR-017**: Frontend application shell MUST update navigation controls and visible action buttons dynamically based on the authenticated user's effective permissions while preserving server-side authorization enforcement.
- **FR-018**: System MUST provide seed initialization with an initial bootstrap administrator account (`admin`) configured via secure environment variables or a guided first-run prompt.

---

### Non-Functional Requirements

- **NFR-001 (On-Premises / Offline Independence)**: Authentication and session verification MUST NOT require public internet access, external auth providers, or hosted third-party services (Constitution Principle 1).
- **NFR-002 (Security & Defense-in-Depth)**: Passwords must use Argon2id; session tokens must be cryptographically secure and unguessable (minimum 256 bits entropy); sensitive attributes must be masked in logs.
- **NFR-003 (Performance)**: Session validation overhead on API requests MUST add less than 5ms latency. Password hashing MUST balance brute-force resistance with reasonable server CPU utilization (target ~200-400ms per verification).
- **NFR-004 (Auditability)**: All access control and authentication changes MUST be durable, immutable, and queryable by authorized auditors with timestamps and client IP addresses.

---

### Key Entities

- **User**: Represents a catalog account with identity attributes (`id`, `username`, `email`, `password_hash`, `is_active`, `is_superuser`, timestamps).
- **Role**: Represents a named set of permissions (`id`, `code`, `name`, `description`, `is_system`).
- **Permission**: Atomic capability code (`id`, `code`, `name`, `module`, `description`).
- **UserRole**: Association mapping users to assigned roles.
- **CategoryScopeGrant**: Association granting a role or user specific permissions over a category hierarchy.
- **SourceScopeGrant**: Association granting a role or user specific permissions over a direct data source.
- **UserSession**: Represents an active authenticated session (`id`, `user_id`, `token_hash`, `created_at`, `expires_at`, `last_activity_at`, `is_revoked`).
- **SecurityAuditEvent**: Immutable audit log entry (`id`, `event_type`, `user_id`, `actor_id`, `target_resource`, `status`, `ip_address`, `timestamp`, `details`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of protected API endpoints reject unauthenticated requests with HTTP 401 and unauthorized requests with HTTP 403.
- **SC-002**: Password verification uses Argon2id with 0 plaintext credentials stored or logged.
- **SC-003**: An authenticated user with inherited parent category permissions can access descendant resources with zero manual sub-grant configuration.
- **SC-004**: Password changes and administrative revocations invalidate 100% of target user sessions across all active devices within 1 second.
- **SC-005**: 100% of security audit events (logins, lockouts, permission edits) are captured in the immutable audit table.

---

## Assumptions

- Users authenticate via local username/password accounts stored directly in the central PostgreSQL database.
- Enterprise directory integration (AD/LDAP/SAML/OAuth SSO) is deferred and explicitly excluded from this release per Constitution Principle 5.
- Client browsers communicate with the backend API over HTTPS (or local HTTP during development).
