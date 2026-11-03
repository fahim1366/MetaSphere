# Data Model & Configuration Schemas: Project Foundation

**Feature**: `001-project-foundation`  
**Date**: 2026-11-02  
**Status**: Completed  

This document defines the core data contracts, Pydantic schemas, configuration models, and secret-redaction rules for the initial MetaSphere Project Foundation. In accordance with strict scope exclusions, no database catalog entities (tables, columns, schemas, sources) or authentication entities are defined in this baseline.

---

## 1. Pydantic Schemas & DTOs

### 1.1 Health Check Entities

#### `ComponentStatus`
Represents the runtime connectivity and latency of an underlying infrastructure dependency. Matches `specs/001-project-foundation/contracts/health-api.json`.

| Field | Type | Required | Description | Example / Constraints |
|---|---|---|---|---|
| `name` | `str` | Yes | Identifier of the monitored component | `"postgres"`, `"redis"` |
| `status` | `str` | Yes | Connectivity state | `"connected"`, `"disconnected"`, `"error"` |
| `latency_ms` | `float | null` | Optional | Measured ping round-trip latency in milliseconds | `1.45` (>= 0.0) |
| `error` | `str | null` | Optional | Sanitized error message if disconnected (no credentials or internal host details) | `"Connection refused"`, `"Query timeout"` |

#### `HealthLiveResponse`
Response schema for `GET /health/live`. Indicates that the FastAPI ASGI process is alive and responsive. Evaluated purely in-memory (< 5ms response latency).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `status` | `str` | Yes | Liveness indicator | `"live"` |
| `timestamp` | `datetime` | Yes | UTC timestamp in ISO 8601 format | `"2026-11-02T12:00:00Z"` |
| `service` | `str` | Yes | Application service identifier | `"metasphere-backend"` |
| `version` | `str` | Yes | Backend application version | `"0.1.0"` |

#### `HealthReadyResponse`
Response schema for `GET /health/ready`. Indicates whether dependencies required to serve requests are fully accessible. Probed concurrently over warm connection pools (P95 < 25ms local design target; driver socket timeout ceiling at 2.0s).

| Field | Type | Required | Description | Example / Constraints |
|---|---|---|---|---|
| `status` | `str` | Yes | Overall readiness indicator | `"ready"` (all healthy) or `"unhealthy"` (any failed) |
| `timestamp` | `datetime` | Yes | UTC timestamp in ISO 8601 format | `"2026-11-02T12:00:00Z"` |
| `components` | `dict[str, ComponentStatus]` | Yes | Map of dependency statuses keyed by component name | `{"postgres": {...}, "redis": {...}}` |

**Validation Rules & Status Transitions:**
- If all monitored components report `status == "connected"`, the overall `status` MUST be `"ready"` and the HTTP status code MUST be `200 OK`.
- If any component reports `status != "connected"`, the overall `status` MUST be `"unhealthy"` and the HTTP status code MUST be `503 Service Unavailable`.
- Error messages in `error` MUST be sanitized to prevent leaking database usernames, passwords, or internal network topology.

### 1.2 Sanitized Error Model

#### `ErrorResponse`
Standard schema for unhandled errors and service failures.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `detail` | `str` | Yes | Sanitized, client-safe error description | `"Internal server error"`, `"Database connection unavailable"` |
| `correlation_id` | `str` | Yes | Unique UUID4 string matching server-side structured logs | `"d3b07384-d113-4c9f-8a2b-2d4e8c6e2a1b"` |

---

## 2. Application Configuration Model (`ApplicationSettings`)

Implemented using `pydantic-settings` (`BaseSettings`) in `backend/app/core/config.py`. Configuration is read from environment variables or a local `.env` file with strict type validation.

| Setting Name | Type | Default | Description | Environment Scope |
|---|---|---|---|---|
| `APP_NAME` | `str` | `"MetaSphere Enterprise Data Catalog"` | Human-readable application name | All |
| `APP_ENV` | `str` | `"development"` | Environment identifier (`development`, `test`, `production`) | All |
| `DEBUG` | `bool` | `False` | Debug mode toggle (must be `False` in production) | Dev / Test only |
| `API_V1_PREFIX` | `str` | `"/api/v1"` | Base route prefix for API endpoints | All |
| `HOST` | `str` | `"0.0.0.0"` | Bind address for FastAPI server | All |
| `PORT` | `int` | `8000` | Port for FastAPI server | All |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:4200"]` | Allowed origins for cross-origin requests | Dev default; strict in prod |
| `POSTGRES_HOST` | `str` | `"localhost"` | Host for PostgreSQL service | All |
| `POSTGRES_PORT` | `int` | `5432` | Port for PostgreSQL service | All |
| `POSTGRES_DB` | `str` | `"metasphere_catalog"` | Central metadata database name | All |
| `POSTGRES_USER` | `str` | `"postgres"` | Database user (development default) | Must be overridden in prod |
| `POSTGRES_PASSWORD` | `SecretStr` | `"postgres"` | Database password (development default) | Stored as `SecretStr`, never serialized |
| `DB_POOL_SIZE` | `int` | `10` | Process-local connection pool baseline | Production / Tuning |
| `DB_MAX_OVERFLOW` | `int` | `20` | Process-local overflow capacity | Production / Tuning |
| `DB_POOL_TIMEOUT` | `float` | `2.0` | Timeout waiting for pool connection | Production / Tuning |
| `REDIS_HOST` | `str` | `"localhost"` | Host for Redis broker & cache | All |
| `REDIS_PORT` | `int` | `6379` | Port for Redis broker & cache | All |
| `REDIS_DB` | `int` | `0` | Redis database index | Standard default |
| `CELERY_BROKER_URL` | `str | None` | Computed from Redis settings | Broker URL for Celery |
| `CELERY_RESULT_BACKEND` | `str | None` | Computed from Redis settings | Result backend URL for Celery |
| `LOG_LEVEL` | `str` | `"INFO"` | Logging severity level | All |

### 2.1 Independent Environment Expectations
- **Development (`APP_ENV="development"`)**:
  - `DEBUG=True` is permitted.
  - Development defaults (`postgres:postgres` on `localhost`) are accepted.
  - `CORS_ORIGINS` includes local development ports (e.g. `http://localhost:4200`).
- **Testing (`APP_ENV="test"`)**:
  - `DEBUG=False`.
  - Database targets an isolated test database (`metasphere_test`).
  - Redis mocks or test database index (`REDIS_DB=15`) are utilized.
- **Production (`APP_ENV="production"`)**:
  - `DEBUG` MUST be `False`.
  - Non-default, cryptographically sound database credentials MUST be supplied via environment variables.
  - `CORS_ORIGINS` MUST list explicit internal domain origins (e.g., `["https://catalog.internal.org"]`). Wildcards (`*`) and `localhost` are rejected at process boot.

### 2.2 Production Startup Validation Rules
Enforced via `@model_validator(mode="after")` in `backend/app/core/config.py`:
```python
@model_validator(mode="after")
def validate_production_settings(self) -> Self:
    if self.APP_ENV == "production":
        if self.DEBUG:
            raise ValueError("DEBUG must be False in production environment")
        
        insecure_passwords = {"postgres", "password", "admin", "123456", ""}
        if self.POSTGRES_PASSWORD.get_secret_value() in insecure_passwords:
            raise ValueError("Insecure default POSTGRES_PASSWORD rejected in production")
            
        for origin in self.CORS_ORIGINS:
            if "*" in origin or "localhost" in origin or "127.0.0.1" in origin:
                raise ValueError(f"Unsafe CORS origin '{origin}' rejected in production")
    return self
```

### 2.3 SecretStr Limitations & Explicit Redaction Rules
`SecretStr` prevents accidental exposure in Pydantic `str()` or `repr()` outputs. However, it does not prevent third-party loggers or unhandled driver exceptions from logging connection strings containing credentials. Therefore, the following defense-in-depth rules are enforced:

1. **Logging Filter (`SecretMaskingFilter`)**: Attached to root logging handlers:
   - Sanitizes connection strings matching `r'(://[^:]+:)([^@]+)(@)'` to `r'\1***\3'`.
   - Sanitizes key-value strings matching `r'(?i)(password|secret|token|key)[=\s:]+["\']?([^"\'\s,;]+)'` to `r'\1=***'`.
   - Sanitizes bearer authorization headers matching `r'(?i)(bearer\s+)[A-Za-z0-9_\-\.]+'` to `r'\1***'`.
2. **SQLAlchemy Logging**: `echo=False` is hardcoded across all environments. If the database URL is logged at startup, it MUST use `engine.url.render_as_string(hide_password=True)`.
3. **Exception Handler**: All unhandled exceptions are caught by FastAPI global handlers, logged internally with redacted tracebacks, and mapped to the generic `ErrorResponse` schema with a `correlation_id`.

### 2.4 Synchronous Database Engine & Connection Budgeting
- Driver: `postgresql+psycopg2://`
- Assembled property: `sqlalchemy_database_url`
- Driver socket timeout: `connect_args={"connect_timeout": 2}`
- Statement timeout: session `options="-c statement_timeout=2000"`
- Pool parameters: role-specific budgets (`pool_pre_ping=True`, `pool_recycle=1800`, `pool_timeout=2.0`):
  - API processes: `pool_size=10`, `max_overflow=0`
  - Celery worker processes: `pool_size=5`, `max_overflow=0`
- **Process-Local Pool Budgeting**:
  - 4 Uvicorn API workers $\times$ 10 max connections = 40 connections.
  - 4 Celery concurrency workers $\times$ 5 max connections = 20 connections.
  - Peak application load = 60 connections.
  - PostgreSQL `max_connections` configured to `150` in production Compose to maintain a safe 90-connection operational buffer.

---

## 3. Celery Task Contracts

### 3.1 `HealthCheckTaskPayload`
Payload for baseline asynchronous worker verification. Matches `specs/001-project-foundation/contracts/celery-task.json`.

| Field | Type | Description |
|---|---|---|
| `ping_id` | `str` | Unique UUID string identifying the test execution |
| `sent_at` | `datetime` | UTC timestamp of dispatch |

### 3.2 `HealthCheckTaskResult`
Result structure stored in Redis upon task completion. Matches `specs/001-project-foundation/contracts/celery-task.json`.

| Field | Type | Description |
|---|---|---|
| `ping_id` | `str` | Echoed UUID string |
| `status` | `str` | `"pong"` |
| `worker_name` | `str` | Hostname or node name of the executing Celery worker |
| `completed_at` | `datetime` | UTC timestamp of execution completion |
| `duration_ms` | `float` | Task processing duration in milliseconds |
