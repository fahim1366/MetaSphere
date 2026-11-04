# Architectural Research & Technology Decisions: Authentication & Access Control

**Feature**: `002-authentication-access-control`  
**Date**: 2026-11-03  
**Status**: Approved Baseline  

---

## 1. Password Hashing Algorithm & Security Parameters

### Decision
Standardize password hashing on **Argon2id** using the standard `argon2-cffi` library, strictly complying with **Constitution Principle 5**.

```python
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # 3 iterations
    memory_cost=65536,  # 64 MiB RAM
    parallelism=4,      # 4 concurrent threads
    hash_len=32,        # 32-byte derived key
    salt_len=16,        # 16-byte cryptographically secure salt
)
```

### Rationale
- **Argon2id** is the OWASP-recommended password hashing function, combining resistance against GPU cracking (memory-hard Argon2d) and side-channel timing attacks (Argon2i).
- `argon2-cffi` is a standard, battle-tested Python CFFI wrapper, already compiled and supported across Windows, Linux, and air-gapped environments without external network dependencies.
- **Timing Protection**: Verification takes ~200-300ms on server CPUs, neutralizing rapid brute-force attacks while remaining scalable for 600 concurrent users.

### Alternatives Considered
- `bcrypt`: Rejected because it has a hard limit of 72 bytes on password length and lacks memory-hardness against modern ASIC/GPU cracking.
- `PBKDF2-HMAC-SHA256`: Rejected because it lacks memory-hardness; vulnerable to GPU-accelerated dictionary attacks.

---

## 2. Session Architecture, Tokens & Instant Revocation

### Decision
Implement a **hybrid stateful session model**:
1. Upon successful login, the server generates a cryptographically random 256-bit entropy token (`secrets.token_urlsafe(32)`).
2. The raw token is returned to the client and transmitted via `Authorization: Bearer <token>` (or an HttpOnly cookie).
3. The server computes the SHA-256 hash of the token (`token_hash = sha256(token).hexdigest()`) and stores the session record in PostgreSQL (`app_user_session`) and caches active tokens in Redis (`session:<token_hash>`).
4. **Instant Revocation**:
   - Individual logout deletes the token from Redis and marks `is_revoked = True` in PostgreSQL.
   - Password change or admin revocation flags all sessions for the `user_id` as revoked in the database and prunes them from Redis in `< 50ms`.

### Rationale
- Pure stateless JWTs cannot be reliably revoked immediately without a distributed revocation blacklist. In an enterprise catalog where account compromises or permissions changes must take effect immediately, stateful sessions (backed by Redis cache + PostgreSQL persistence) guarantee instantaneous revocation.
- Storing only the SHA-256 hash of session tokens in the database ensures that a database dump or backup does not expose active session tokens.

### Alternatives Considered
- Stateless JWTs: Rejected because tokens cannot be revoked before expiration without maintaining a stateful blacklist, which negates the stateless benefit.
- Session Cookies only: Allowed in browsers, but Bearer tokens provide uniform API access for both the Angular SPA and automated CLI/service clients.

---

## 3. Role-Based Access Control (RBAC) & Hierarchy Inheritance

### Decision
Implement explicit, multi-role RBAC with hierarchical category inheritance:
- **Users to Roles**: Many-to-Many (`app_user_role`).
- **Roles to Permissions**: Many-to-Many (`app_role_permission`).
- **Permissions**: Atomic string codes (e.g. `CATALOG_READ`, `CATALOG_WRITE`, `SOURCE_MANAGE`, `USER_MANAGE`, `ROLE_MANAGE`, `AUDIT_READ`).
- **Category Hierarchy Scoping**:
  - Permissions can be granted globally or scoped to a `category_id`.
  - When granted on a parent category, the system evaluates category ancestry via PostgreSQL recursive CTEs (or materialized path `lineage_path`), automatically granting permissions to all child categories and their contained data sources.
- **Server-Side Enforcement**:
  - Implemented as FastAPI dependency: `def require_permissions(*required_permissions: str)`.
  - Deny by default: if a request does not possess all required permissions, it is rejected immediately with HTTP 403 Forbidden.

---

## 4. Account Enumeration & Brute-Force Defense

### Decision
1. **Generic Errors**: Failed login returns HTTP 401 with generic message `{"detail": "Invalid username or password"}` regardless of whether the username exists.
2. **Constant-Time Verification**: When a username does not exist, the server executes a dummy Argon2id hash verification against a pre-computed constant hash to eliminate timing discrepancies between existing and non-existent users.
3. **Progressive Rate Limiting**:
   - Redis sliding window rate limiter tracks failed attempts by `client_ip` and `username`.
   - 5 failed attempts within 5 minutes trigger a 15-minute temporary lockout for the IP/username pair.
