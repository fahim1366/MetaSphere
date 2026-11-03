# Technical Research & Architectural Decisions: Project Foundation

**Feature**: `001-project-foundation`  
**Date**: 2026-11-02  
**Status**: Completed  

---

## 1. Node.js Version & Angular 22 Compatibility

### Decision
Pin the frontend toolchain strictly to **Node.js 22.22.3** (Active LTS) and **npm 10.9.8** (the bundled npm version). Record this exact reproducible patch version across:
- `frontend/.nvmrc`: `22.22.3`
- `frontend/package.json`:
  ```json
  "engines": {
    "node": "=22.22.3",
    "npm": ">=10.9.8"
  }
  ```
- All documentation (`plan.md`, `quickstart.md`, `docs/dev-setup.md`).

### Compatibility Verification & Rationale
- The official Angular version compatibility matrix specifies that **Angular 22 requires Node.js `^22.22.3 || ^24.15.0 || ^26.0.0`**.
- Earlier drafts specifying Node.js minor versions below 22.22.3 fail the Angular CLI engine compatibility check and will block execution.
- Selecting **Node.js 22.22.3** satisfies the `^22.22.3` requirement within the Active LTS line, providing long-term maintenance, stable V8 bytecode execution, and complete native ESM compatibility.
- Pinning the exact patch version (`=22.22.3`) guarantees reproducible builds across Windows developer hosts, CI runners, and air-gapped production packaging environments.

---

## 2. Air-Gapped Deployment Lifecycle & Image Archive Workflow

### Decision
Establish an explicit four-phase operational model distinguishing **offline production runtime** from **offline developer workstations** and **connected staging builds**:

1. **Phase 1: Build & Package (Connected Staging Environment)**:
   - Automated CI or an approved staging build workstation with access to internal/approved mirrors builds the production container images:
     ```bash
     docker build -f backend/Dockerfile -t metasphere-backend:0.1.0 backend/
     docker build -f frontend/Dockerfile -t metasphere-frontend:0.1.0 frontend/
     ```
   - Official base images are pulled: `postgres:16-alpine`, `redis:7-alpine`.
   - All four required production images are exported into a compressed, self-contained archive bundle:
     ```bash
     docker save metasphere-backend:0.1.0 metasphere-frontend:0.1.0 postgres:16-alpine redis:7-alpine | gzip > metasphere-images-v0.1.0.tar.gz
     sha256sum metasphere-images-v0.1.0.tar.gz > metasphere-images-v0.1.0.tar.gz.sha256
     ```
2. **Phase 2: Secure Air-Gap Transit**:
   - The archive bundle and checksum are transferred across the physical air-gap perimeter via organization-approved optical media or secure hardware kiosks following organizational data handling policies.
   - Integrity is verified prior to ingest (`sha256sum -c metasphere-images-v0.1.0.tar.gz.sha256`).
3. **Phase 3: Ingest & Isolated Production Runtime**:
   - On the air-gapped production host or internal registry:
     ```bash
     docker load -i metasphere-images-v0.1.0.tar.gz
     docker compose -f infrastructure/docker-compose.prod.yml up -d
     ```
   - **Zero Outbound Access**: Runtime operation does not attempt external network fetches. Frontend assets (Vazirmatn/Inter fonts, PrimeIcons, scripts) are pre-bundled inside the Nginx container; backend Python packages and database drivers are pre-installed in the backend container.
4. **Phase 4: Offline Developer Workstations**:
   - For developer workstations lacking direct internet access:
     - Python wheels are pre-mirrored into a local wheelhouse directory (`pip install --no-index --find-links=./wheelhouse/ -e ".[dev]"`).
     - Node dependencies are installed from an offline tarball or pre-populated local npm cache (`npm ci --prefer-offline --cache ./npm-cache`).

### Rationale
- Conforms strictly to Constitution Principle 1 (production runtime MUST NOT depend on public internet or CDNs).
- Multi-stage Dockerfiles alone do not guarantee air-gapped readiness; an explicit archive export/load workflow ensures deterministic artifact delivery.

---

## 3. Database Persistence: Synchronous SQLAlchemy 2.x & Connection Budgeting

### Decision
Standardize backend persistence on **Synchronous SQLAlchemy 2.x** using `psycopg2-binary` (PostgreSQL driver) and a tuned synchronous connection pool (`QueuePool`).

```python
engine = create_engine(
    settings.sqlalchemy_database_url,
    connect_args={"connect_timeout": 2},  # Driver-level socket connect timeout (seconds)
    pool_size=settings.DB_POOL_SIZE,       # Process-local pool baseline
    max_overflow=settings.DB_MAX_OVERFLOW, # Process-local overflow capacity
    pool_timeout=2.0,                      # Timeout waiting for pool connection
    pool_pre_ping=True,                    # Validates connection health before issuing queries
    pool_recycle=1800,                     # Recycles connections every 30 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Connection Budgeting Across Processes
SQLAlchemy connection pools are **process-local**. In a multi-worker production deployment:
- **API Server**: $N$ Uvicorn worker processes (e.g., 4). Each worker holds up to `pool_size (5) + max_overflow (5) = 10` connections $\rightarrow 40$ connections peak.
- **Celery Workers**: $M$ concurrency worker processes (e.g., 4). Each worker holds up to `pool_size (2) + max_overflow (3) = 5` connections $\rightarrow 20$ connections peak.
- **Total Application Connections**: $40 + 20 = 60$ peak connections.
- **PostgreSQL Configuration**: PostgreSQL `max_connections` is configured to `150` in `docker-compose.prod.yml` to provide ample headroom above the application ceiling (60) for administrative sessions and migrations.

### Rationale
- Celery background workers and Alembic migrations are inherently synchronous. Using a synchronous driver avoids maintaining dual database engines (async for FastAPI, sync for Celery/Alembic) and eliminates event-loop bridging issues.
- In FastAPI, declaring database-accessing endpoints as standard `def` functions automatically dispatches them to FastAPI's internal worker threadpool, ensuring high throughput for metadata catalog queries without async ORM complexity.

---

## 4. Health & Readiness Probe Architecture & Driver Timeout Safety

### Decision
Explicitly separate **Liveness (`/health/live`)** from **Readiness (`/health/ready`)** with driver-level socket timeouts and bounded concurrency:

1. **Liveness Probe (`GET /health/live`)**:
   - **Responsibility**: Verifies the FastAPI ASGI process is alive and receiving HTTP requests.
   - **Dependencies Checked**: None (pure in-memory check).
   - **Expected Latency**: `< 5ms`.
   - **HTTP Status**: Always `200 OK` while process runs.
2. **Readiness Probe (`GET /health/ready`)**:
   - **Responsibility**: Verifies active connectivity to PostgreSQL and Redis before declaring the service ready.
   - **Driver & Socket Timeout Safety**:
     - Python's `asyncio.wait_for` **cannot cancel** a blocking synchronous socket call executing inside `asyncio.to_thread`. If a database server hangs silently, an async timeout leaves the worker thread blocked indefinitely.
     - To guarantee thread safety and prevent pool exhaustion:
       - **PostgreSQL**: Configured with driver-level socket timeouts: `connect_args={"connect_timeout": 2}` and session `statement_timeout=2000`.
       - **Redis**: Configured with `socket_timeout=2.0` and `socket_connect_timeout=2.0`.
       - With driver socket timeouts set to 2.0s, the blocking C-socket call itself unblocks and raises an exception within 2 seconds, ensuring worker threads are never orphaned.
   - **Concurrency Strategy**: The readiness check runs the PostgreSQL probe (`SELECT 1`) and the Redis probe (`PING`) concurrently using a dedicated, bounded `ThreadPoolExecutor(max_workers=4)`.
   - **Performance Target**:
     - Over pre-warmed connection pools with `pool_pre_ping=True`, local healthy execution of `SELECT 1` and `PING` completes in 1–3ms.
     - **P95 < 25ms locally** is documented as a design performance target to be validated via automated latency benchmark tests (`test_health_bench.py`), not an assumed guarantee.
     - The **2.0-second timeout** represents the maximum circuit-breaker ceiling on dependency outage before returning `HTTP 503`.

---

## 5. Frontend Test Runner: Vitest

### Decision
Standardize exclusively on **Vitest** for frontend unit testing.

- **Test Runner**: Vitest with `@analogjs/vite-plugin-angular` (or Angular CLI modern test builder).
- **Execution Command (Single Run / CI)**: `npm run test` (`vitest run`).
- **Execution Command (Interactive Watch)**: `npm run test:watch` (`vitest`).
- **Coverage Command**: `npm run test:coverage` (`vitest run --coverage`).

### Rationale
- **Headless & Browserless**: Vitest executes directly in Node.js 22 LTS via jsdom/happy-dom. It does **not** require downloading or launching a heavy Chrome/Chromium binary, which is essential for locked-down and air-gapped CI environments where browser installations fail.
- **Speed & Native ESM**: Instant startup and fast test execution leveraging native Node.js ESM.
- **Modern Test Runner**: Vitest provides native ESM integration and aligns with modern Angular unit testing guidance.

---

## 6. Configuration Security, Credential Rejection & Secret Redaction

### Decision
Implement defense-in-depth configuration security combining Pydantic validation, explicit secret masking filters, and sanitized API exception handlers:

1. **Production Startup Validation (`ApplicationSettings`)**:
   - Enforce an explicit `@model_validator(mode="after")` that rejects unsafe development configurations when `APP_ENV == "production"`:
     - Rejects `DEBUG == True` with a fatal validation error.
     - Rejects known development passwords (`"postgres"`, `"password"`, `"admin"`, `"123456"`, or empty strings) with a fatal validation error.
     - Rejects wildcard (`*`) or `localhost` origins in `CORS_ORIGINS`.
2. **Logging Secret Redaction Filter (`SecretMaskingFilter`)**:
   - `SecretStr` prevents accidental `str()` leaks from Pydantic models, but unhandled exceptions from drivers or HTTP clients could still print connection URIs or headers into logs.
   - A custom `SecretMaskingFilter` is attached to all root logging handlers. It applies regex substitutions to scrub:
     - Passwords in connection URIs (`postgresql://user:***@host:port/db`)
     - Common secret patterns (`password=***`, `secret=***`, `token=***`, `Authorization: Bearer ***`)
   - SQLAlchemy engine logging is configured with `echo=False` across all environments.
3. **Sanitized Error Responses**:
   - Centralized FastAPI exception handlers catch unhandled exceptions, log the full sanitized traceback with a unique `correlation_id`, and return a generic client response (`{"detail": "Internal server error", "correlation_id": "..."}`) with `HTTP 500`.
   - Datastore connection errors are mapped to safe diagnostic messages without leaking hostnames, ports, or usernames.

---

## 7. Single Application Schema in PostgreSQL & Alembic Baseline

### Decision
Initialize PostgreSQL with a single application schema (`public`). Establish the Alembic migration framework (`backend/alembic/`) with a verified baseline revision (`0001_initial_baseline.py`) containing the initial infrastructure setup, and verify both `upgrade` and `downgrade` operations.

### Rationale
- Conforms to Constitution Principle 8: "Start with one application schema... Do not create one schema per source database, user, or Python package by default."
- Establishes version-controlled schema evolution from the initial commit, preventing manual DDL drift.
