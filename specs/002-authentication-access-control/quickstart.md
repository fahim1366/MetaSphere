# Quickstart & Verification Guide: Authentication & Access Control

**Feature**: `002-authentication-access-control`  
**Date**: 2026-11-03  

This guide provides runnable curl scenarios to verify local authentication, role-based access control, session revocation, and security audit logs.

---

## 1. Prerequisites

Ensure local infrastructure and the backend API are running:
```bash
# In terminal 1:
docker compose -f infrastructure/docker-compose.yml up -d

# In terminal 2:
cd backend
source .venv/Scripts/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

---

## 2. Verification Scenarios

### Scenario 1: Initial Admin Login & Token Retrieval
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "AdminPassword123!"}'
```
**Expected Response**: `HTTP 200 OK`
```json
{
  "access_token": "<random_token_string>",
  "token_type": "bearer",
  "expires_at": "...",
  "user": {
    "username": "admin",
    "roles": ["ROLE_SUPER_ADMIN"],
    "permissions": ["CATALOG_READ", "CATALOG_WRITE", "SOURCE_MANAGE", "USER_MANAGE", "ROLE_MANAGE", "AUDIT_READ"]
  }
}
```

### Scenario 2: Unauthenticated Access Rejection (Deny by Default)
```bash
curl -i -X GET http://localhost:8000/api/v1/users
```
**Expected Response**: `HTTP 401 Unauthorized`

### Scenario 3: Verify Current Identity (`/auth/me`)
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```
**Expected Response**: `HTTP 200 OK` with user profile and effective permissions.

### Scenario 4: Unauthorized Access Rejection (HTTP 403 Forbidden)
Attempting an administrative endpoint with a standard user lacking `USER_MANAGE`:
```bash
curl -i -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <regular_user_token>" \
  -H "Content-Type: application/json" \
  -d '{"username": "new_user", "email": "test@example.com", "password": "Password123!"}'
```
**Expected Response**: `HTTP 403 Forbidden`

### Scenario 5: Password Change & Instant Session Invalidation
```bash
# Change password:
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "AdminPassword123!", "new_password": "NewAdminPassword987@"}'

# Prior token must immediately fail:
curl -i -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```
**Expected Response**: `HTTP 401 Unauthorized` (Session revoked).

### Scenario 6: Security Audit Log Inspection
```bash
curl -X GET http://localhost:8000/api/v1/audit/security \
  -H "Authorization: Bearer <new_admin_token>"
```
**Expected Response**: `HTTP 200 OK` showing immutable audit events for all login, logout, and password change attempts.
