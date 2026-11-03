# Implementation Plan: Project Foundation

**Branch**: `001-project-foundation` | **Date**: 2026-11-02 | **Spec**: [specs/001-project-foundation/spec.md](spec.md)

**Input**: Feature specification from `specs/001-project-foundation/spec.md`

## Summary

Establish the initial runnable, maintainable, and testable development foundation for the MetaSphere Enterprise Data Catalog. The feature delivers:
1. Strict monorepo layout (`/backend`, `/frontend`, `/infrastructure`, `/docs`, `/scripts`).
2. Python 3.12 / FastAPI backend foundation using synchronous SQLAlchemy 2.x with `psycopg2-binary` and centralized Pydantic Settings with fail-closed production validation.
3. Angular 22 Single Page Application frontend (pinned to Node.js 22.22.3 Active LTS and npm 10.9.8) using Standalone Components, PrimeNG, Tailwind CSS 4, and bidirectional (RTL/LTR) shell layout tested exclusively via Vitest.
4. Central PostgreSQL 16+ repository setup (single application schema `public`) with Alembic baseline migration.
5. Redis 7+ and Celery background task processing infrastructure with a verifiable baseline health task.
6. Local development environment supporting the approved **Hybrid workflow** (PostgreSQL & Redis in Docker Compose; FastAPI & Angular running natively on the Windows host).
7. Separate air-gapped image archive packaging and ingest workflow (`docker save` / `docker load`) for 100% offline production deployment across four container images.
8. Distinct `/health/live` (< 5ms) and `/health/ready` (concurrent probe, P95 < 25ms target, driver socket timeouts with 2.0s circuit-breaker ceiling) observability probes.
9. Sanitized logging filter (`SecretMaskingFilter`) and global exception handlers preventing credential leaks.
10. Automated quality gates (Ruff, Mypy, Vitest, Pytest) and developer onboarding documentation.

All data catalog business features, authentication, authorization, connectors, metadata extraction, and AI integration are strictly excluded.

## Technical Context

**Language/Version**:
- Backend: Python 3.12 (pinned in `.python-version` and `pyproject.toml`)
- Frontend: TypeScript strict mode / Node.js 22.22.3 Active LTS, npm 10.9.8 (pinned in `.nvmrc` and `package.json` engines)
**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, Pydantic v2, Pydantic Settings, SQLAlchemy 2.x (synchronous), Alembic, Celery 5.x, Redis-py, Psycopg2-binary
- Frontend: Angular 22, PrimeNG, Tailwind CSS 4, PrimeIcons, RxJS, Angular Signals, Vitest
**Storage & Broker**:
- PostgreSQL 16+ (central metadata repository, single application schema `public`)
- Redis 7+ (broker & result backend)
**Database Access Architecture**:
- Synchronous SQLAlchemy 2.x engine (`QueuePool`, `pool_pre_ping=True`, role-specific budgets: API `pool_size=10, max_overflow=0`, Celery `pool_size=5, max_overflow=0`, `pool_timeout=2.0`, `connect_args={"connect_timeout": 2}`)
- Process-local connection budgeting: sized for API workers and Celery concurrency limits against PostgreSQL `max_connections=150`
- Session management: `sessionmaker(bind=engine)` injected via standard FastAPI `def get_db()` dependency
- Uniformity across FastAPI route handlers, Celery background tasks, and Alembic migrations
**Testing & Quality**:
- Backend: Pytest, HTTPX (TestClient), Pytest-benchmark, Ruff (linting & formatting), Mypy (strict type analysis)
- Frontend: Vitest (headless, browserless ESM execution), ESLint
**Target Platform**:
- Local Development: Windows host (Hybrid workflow: host app servers + Docker Compose datastores)
- Production: On-premises Linux containers (air-gapped, zero public internet access)
**Project Type**: Monorepo Web Application (FastAPI REST service + Angular SPA + Celery worker)
**Performance Targets**:
- Process Liveness (`/health/live`): < 5ms response latency
- Dependency Readiness (`/health/ready`): Healthy P95 latency < 25ms locally as a design target (to be verified via automated benchmark) via concurrent execution across pre-warmed connection pools
- Driver Socket Timeout & Circuit-Breaker Ceiling: 2.0-second timeout at the driver socket level before returning HTTP 503 on partition
- Local Application Startup: < 5 seconds for backend and frontend
- Celery Verification Task Roundtrip: < 2 seconds
**Security & Constraints**:
- Strict adherence to Constitution v1.0.0 (all 14 non-negotiable principles)
- Fail-closed configuration: production startup rejects default credentials, `DEBUG=True`, and unsafe CORS
- Secret masking: custom logging filter scrubs credentials from URIs and exception tracebacks
- Client-rendered SPA only (no SSR, SSG, or hydration)
- Production runtime: 100% offline independence (locally bundled fonts and icons; pre-packaged container images)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement Summary | Architectural Compliance | Status |
|---|---|---|:---:|
| **1. On-Premises & Dependencies** | No public internet, CDNs, or external fonts at runtime; all assets bundled locally. | Frontend packages Vazirmatn/Inter fonts and PrimeIcons locally in `src/assets/`. Production container images pre-packaged via archive bundle (`docker save`/`load`). | **PASS** |
| **2. Approved Stack & Boundaries** | Angular 22, PrimeNG, Tailwind 4, Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL, Celery, Redis. Monorepo layout. No Java/Spring/ngbase. | Exact approved technology stack configured. Strict monorepo boundaries maintained. No forbidden libraries. | **PASS** |
| **3. Metadata-First Discovery** | Read-only discovery; no business row replication. | Discovery and extraction are strictly excluded from this foundation feature. | **PASS** |
| **4. Preserve Source Semantics** | Retain vendor types and model document DBs properly. | Connectors and metadata models are strictly excluded from this feature. | **PASS** |
| **5. Security & Least Privilege** | Fail-closed, Argon2id, encrypted credentials, no secrets in code/logs. | Configuration uses Pydantic Settings with `SecretStr`; production rejects default credentials; `SecretMaskingFilter` scrubs logs; `.env` excluded. | **PASS** |
| **6. Explicit API Contracts** | Thin routers, Pydantic schemas, no exposed ORM models, explicit pagination/errors. | `/health/live` and `/health/ready` use explicit Pydantic response models and OpenAPI 3.1 specifications. | **PASS** |
| **7. Background Extraction** | Celery + Redis, observable state, idempotency, bounded retries. | Celery worker and Redis broker initialized with structured task contracts and error isolation. | **PASS** |
| **8. PostgreSQL Integrity** | Single application schema `public`, Alembic migrations, UUID defaults, UTC timestamps. | PostgreSQL initialized in single schema `public`; Alembic baseline migration established with bidirectional checks. | **PASS** |
| **9. Audit History & Observability** | Traceable events, distinct liveness/readiness probes, health metrics. | Distinct `/health/live` (<5ms) and `/health/ready` (concurrent, P95 <25ms target, 2s driver ceiling) endpoints implemented with structured payloads. | **PASS** |
| **10. Accessible Angular UX** | Client-rendered SPA (no SSR), PrimeNG, Tailwind 4, Persian RTL & English LTR support. | SPA architecture; CSS logical properties; centralized RTL/LTR direction signal; Vitest headless testing; local assets only. | **PASS** |
| **11. Mandatory Testing** | Strict testing required: backend pytest, frontend tests, quality gates; never skip tests. | Pytest, Ruff, Mypy, ESLint, and Vitest configurations established with automated verification scripts. | **PASS** |
| **12. Scale & Performance** | Measured performance; bounded connections and queries. | Bounded health check timeouts (2s driver ceiling); concurrent `SELECT 1` and `PING` probes over pooled connections. | **PASS** |
| **13. AI Disabled** | AI disabled pending organizational approval; no metadata transmission. | AI integration strictly excluded; no AI SDKs, keys, or endpoints configured. | **PASS** |
| **14. Documentation & Decisions** | Explainable decisions, ADRs, reproducible delivery, clear DoD. | Complete research document, quickstart guide, data models, and onboarding docs produced. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/001-project-foundation/
├── spec.md              # Approved feature specification
├── checklists/
│   └── requirements.md  # Requirements quality validation checklist (100% PASS)
├── plan.md              # This technical implementation plan
├── research.md          # Technical research & architectural decisions
├── data-model.md        # Data entities, Pydantic schemas, and configuration models
├── quickstart.md        # Step-by-step developer setup and runnable verification guide
└── contracts/           # API and messaging interface contracts
    ├── health-api.json  # OpenAPI 3.1 specification for /health/live and /health/ready
    └── celery-task.json # JSON Schema specification for Celery verification task
```

### Source Code (repository root)

```text
MetaSphere/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   └── health.py          # /health/live and /health/ready routers
│   │   │   ├── api_router.py          # Central APIRouter wiring
│   │   │   ├── deps.py                # Database session dependency injection (get_db)
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic Settings (ApplicationSettings) with prod validators
│   │   │   ├── logging.py             # Structured logging configuration with SecretMaskingFilter
│   │   │   └── __init__.py
│   │   ├── db/
│   │   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   │   ├── session.py             # Synchronous engine (QueuePool) & SessionLocal
│   │   │   └── __init__.py
│   │   ├── jobs/
│   │   │   ├── celery_app.py          # Celery app initialization with Redis broker
│   │   │   ├── tasks.py               # Baseline health_check_task
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── health.py              # Pydantic models (HealthLiveResponse, HealthReadyResponse)
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   └── main.py                    # FastAPI application, lifespan, CORS, and sanitized error handlers
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_initial_baseline.py # Initial baseline database revision
│   │   ├── env.py                     # Synchronous Alembic migration environment
│   │   └── script.py.mako             # Migration template
│   ├── tests/
│   │   ├── conftest.py                # Pytest fixtures (TestClient, DB session, Redis mock)
│   │   ├── api/
│   │   │   ├── test_health.py         # Integration tests for /health/live and /health/ready
│   │   │   └── test_health_bench.py   # Latency benchmark verifying P95 < 25ms locally
│   │   └── unit/
│   │       ├── test_config.py         # Config validation tests (including prod rejection tests)
│   │       └── test_tasks.py          # Celery verification task tests
│   ├── .env.example                   # Sanitized backend environment template
│   ├── alembic.ini                    # Alembic configuration
│   ├── pyproject.toml                 # Pinned dependencies (Python 3.12, FastAPI, Ruff, Mypy)
│   ├── .python-version                # Pinned Python version (3.12)
│   └── Dockerfile                     # Multi-stage production container definition
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── services/
│   │   │   │   │   ├── health.service.ts      # HTTP client service querying /health/ready
│   │   │   │   │   └── direction.service.ts   # Centralized RTL/LTR direction signal manager
│   │   │   │   └── models/
│   │   │   │       └── health.model.ts        # TypeScript interfaces matching HealthReadyResponse
│   │   │   ├── layout/
│   │   │   │   ├── shell.component.ts         # Root shell component with direction binding
│   │   │   │   ├── shell.component.html
│   │   │   │   └── shell.component.scss
│   │   │   ├── features/
│   │   │   │   └── health-dashboard/          # Foundation readiness status dashboard widget
│   │   │   │       ├── health-dashboard.component.ts
│   │   │   │       ├── health-dashboard.component.html
│   │   │   │       └── health-dashboard.component.scss
│   │   │   ├── app.config.ts          # Angular providers (PrimeNG, HttpClient, etc.)
│   │   │   ├── app.routes.ts          # Root routing configuration
│   │   │   └── app.component.ts       # Root bootstrap component
│   │   ├── assets/
│   │   │   ├── fonts/                 # Locally bundled Vazirmatn and Inter fonts
│   │   │   └── icons/                 # Locally bundled PrimeIcons
│   │   ├── index.html
│   │   ├── main.ts
│   │   └── styles.scss                # Tailwind CSS 4 CSS-first import & custom theme
│   ├── tests/
│   │   ├── shell.component.spec.ts    # Vitest unit test for bidirectional shell
│   │   └── health.service.spec.ts     # Vitest unit test for health client
│   ├── .nvmrc                         # Pinned Node.js version (22.22.3)
│   ├── package.json                   # Angular 22, PrimeNG, Tailwind 4, Vitest dependencies
│   ├── tsconfig.json                  # Strict TypeScript configuration
│   ├── eslint.config.js               # Strict ESLint configuration
│   ├── vitest.config.ts               # Vitest configuration (headless, jsdom/happy-dom)
│   └── Dockerfile                     # Multi-stage production container definition (Nginx)
├── infrastructure/
│   ├── docker-compose.yml             # Local dev: PostgreSQL 16 & Redis 7 services with health checks
│   ├── docker-compose.prod.yml        # Production: Full stack deployment using pre-loaded images
│   └── nginx/
│       └── nginx.conf                 # Production reverse proxy & static asset serving
├── docs/
│   ├── dev-setup.md                   # Complete local setup & onboarding guide
│   ├── AGENTS-reference.md
│   └── constitution-fa.md
├── scripts/
│   ├── verify.ps1                     # Root offline build, lint, and test runner
│   └── package-airgap.sh              # Script to build and export production image archive bundle
├── .gitignore                         # Strict exclusion of .env, venvs, dist, logs
└── README.md                          # Repository mission, quick links, and architecture overview
```

**Structure Decision**: Monorepo with dedicated `/backend`, `/frontend`, `/infrastructure`, `/docs`, and `/scripts` directories. Fully satisfies Constitution Principle 2 and AGENTS.md Section 1.3.

---

## Architectural Decisions & Design Details

### 1. Hybrid Development Workflow Architecture
- **Infrastructure Services**: Run via Docker Compose (`infrastructure/docker-compose.yml`).
  - `postgres`: PostgreSQL 16 Alpine, port `5432:5432`, volume `postgres_data`, health check `pg_isready -U postgres`.
  - `redis`: Redis 7 Alpine, port `6379:6379`, volume `redis_data`, health check `redis-cli ping`.
- **Application Services**: Run natively on the Windows host.
  - Backend: `uvicorn app.main:app --reload --port 8000` inside `.venv` (Python 3.12).
  - Background Worker: `celery -A app.jobs.celery_app worker --loglevel=info -P solo` inside `.venv`.
  - Frontend: `npm start` (Angular CLI `ng serve --port 4200`) under Node.js 22.22.3 Active LTS.

### 2. Dual Scope of Dockerfiles & Air-Gapped Lifecycle
- `backend/Dockerfile` and `frontend/Dockerfile` are **not** used for daily local code editing.
- They serve strictly for:
  1. Continuous Integration (CI) automated image packaging.
  2. Production and air-gapped on-premises deployments.
- **Air-Gapped Delivery Workflow**:
  - Connected Staging: Images built and packaged via `docker save` into a compressed archive (`metasphere-images-v0.1.0.tar.gz`) containing:
    1. `metasphere-backend:0.1.0`
    2. `metasphere-frontend:0.1.0`
    3. `postgres:16-alpine`
    4. `redis:7-alpine`
  - Transfer: Approved secure transit across the physical/network air-gap boundary with SHA-256 integrity verification.
  - Ingest: Imported via `docker load -i metasphere-images-v0.1.0.tar.gz` and run via `docker compose -f infrastructure/docker-compose.prod.yml up -d` without outbound internet access.

### 3. Synchronous Database Access Architecture
- Backend persistence standardizes on synchronous SQLAlchemy 2.x with `psycopg2-binary`.
- Engine uses `QueuePool` with `connect_args={"connect_timeout": 2}`, `pool_pre_ping=True`, `pool_timeout=2.0`, and `pool_recycle=1800`.
- Connection budgets are managed per process: API workers (4 workers $\times$ 10 connections = 40 max) and Celery workers (4 workers $\times$ 5 connections = 20 max) operate safely within PostgreSQL's configured `max_connections=150`.
- FastAPI route handlers interact with the database using standard `def` functions dispatched to FastAPI's internal worker threadpool.
- Ensures 100% architectural uniformity with Celery background worker tasks and Alembic migrations.

### 4. Configuration Security, Credential Rejection & Secret Redaction
- **Production Credential Rejection**: Pydantic `@model_validator(mode="after")` rejects `DEBUG=True`, default passwords (`postgres`, `password`, `admin`, empty), and wildcard/localhost CORS origins when `APP_ENV == "production"`.
- **Secret Masking Filter**: Custom `SecretMaskingFilter` attached to logging handlers sanitizes database URIs (`postgresql://user:***@host:port/db`), bearer tokens, and exception tracebacks.
- **Error Sanitization**: Global exception handlers catch unhandled errors, log sanitized tracebacks with a correlation ID, and return a generic `HTTP 500` response to clients (`ErrorResponse`).

### 5. Health & Readiness Observability & Driver Timeout Safety
- **Liveness (`/health/live`)**: In-memory process check responding in `< 5ms`.
- **Readiness (`/health/ready`)**:
  - Probes PostgreSQL (`SELECT 1`) and Redis (`PING`) **concurrently** via a dedicated `ThreadPoolExecutor(max_workers=4)`.
  - Driver-level socket timeouts (`connect_timeout=2` for PostgreSQL, `socket_timeout=2.0` for Redis) guarantee that blocking C-socket calls abort within 2.0s, eliminating the risk of orphaned threads under `asyncio.to_thread`.
  - Healthy response performance: P95 latency **`< 25ms` locally as a design target** (verified via automated latency benchmark tests `test_health_bench.py`).
  - Circuit-breaker ceiling: 2.0-second driver socket timeout before returning `HTTP 503 Service Unavailable`.

### 6. Frontend Toolchain & Vitest Testing
- Frontend pinned strictly to **Node.js 22.22.3 Active LTS** and **npm 10.9.8**, fulfilling Angular 22.0.x engine requirements.
- Testing standardized on **Vitest** (headless, browserless, native ESM).
- Eliminates heavy browser installation requirements in air-gapped CI environments.
- Commands: `npm run test` (single run), `npm run test:watch` (interactive), `npm run test:coverage`.

---

## Risk Analysis & Mitigation Strategy

| Risk | Impact | Probability | Mitigation Strategy |
|---|---|:---:|---|
| **Windows Celery Prefork Limitation** | High | High | Celery default prefork pool encounters process-forking limitations on Windows. Mitigated by prescribing `-P solo` or `-P threads` for local Windows development in documentation and scripts, while retaining prefork for Linux production containers. |
| **Air-gapped Production Dependencies** | Critical | Low | On-premises deployment cannot pull fonts, icons, or wheels from the internet. Mitigated by bundling fonts and icons locally in `frontend/src/assets/`, pinning exact lockfiles, and using pre-packaged image archives (`docker save`/`load`). |
| **Startup Race Conditions in Compose** | Medium | Medium | Backend might boot before datastores finish initializing. Mitigated by Docker health checks with `service_healthy` conditions in Compose, and making backend startup non-fatal. |
| **Toolchain Version Drift** | Medium | Low | Developers might use incompatible Python or Node versions. Mitigated by pinning `.python-version` (3.12), `.nvmrc` (22.22.3), `package.json` engines (`=22.22.3`), and validating prerequisites in `docs/dev-setup.md`. |

---

## Complexity Tracking

> **No Constitution violations detected.** The implementation uses the simplest maintainable design conforming to approved guidelines:
- Single PostgreSQL schema `public` (avoids multi-schema complexity).
- Synchronous SQLAlchemy persistence across API, Celery, and Alembic (avoids async/sync dual-stack complexity).
- Vitest unit testing (headless, native ESM; eliminates browser binary dependencies in offline/CI environments).
- Ruff replacing separate linters/formatters (reduces toolchain overhead).
- Hybrid workflow using native host tools (eliminates container volume mount synchronization issues on Windows).
- Direct Pydantic models for health contracts (no premature abstractions).
