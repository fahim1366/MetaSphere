# Feature Specification: Project Foundation

**Feature Branch**: `001-project-foundation`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Define the initial Project Foundation feature for the MetaSphere Enterprise Data Catalog. Establish a runnable, maintainable, and testable development foundation for MetaSphere. Scope: 1. Monorepo project structure. 2. Backend foundation using Python and FastAPI. 3. Frontend foundation using Angular 22 Standalone Components. 4. PostgreSQL central metadata repository setup. 5. Redis and Celery background processing infrastructure. 6. Local development environment and Docker configuration. 7. Environment configuration examples. 8. Basic health and readiness endpoints. 9. Automated build, lint, and test foundations. 10. Developer setup and onboarding documentation. Strict exclusions: No authentication, RBAC, connectors, extraction, catalog business features, or AI integration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Workspace Bootstrap & Local Run (Priority: P1)

As a software engineer onboarding to MetaSphere, I want to clone the monorepo and bootstrap a local environment using clear documentation and a single local setup sequence, so that I have a running backend API, frontend SPA, central PostgreSQL database, and Redis background broker on my workstation without tribal knowledge or trial-and-error.

**Why this priority**: Without a deterministic local environment and running foundation services, no subsequent engineering work (connectors, metadata discovery, authentication, UI) can begin.

**Independent Test**: Can be independently verified on a clean development workstation by following `docs/dev-setup.md`, running the containerized infrastructure via Docker Compose, launching the FastAPI backend and Angular frontend development servers, and confirming both applications run and communicate locally.

**Acceptance Scenarios**:

1. **Given** a Windows development machine with Docker, Python 3.12, and Node.js installed, **When** the developer starts the local infrastructure via Docker Compose, **Then** PostgreSQL and Redis containers reach healthy status within 30 seconds.
2. **Given** the local infrastructure is running and a valid `.env` is initialized from `.env.example`, **When** the developer launches the FastAPI backend and Angular frontend natively on the Windows host, **Then** the backend serves the API on the designated port and the frontend renders the initial shell in the browser without console or network errors.

---

### User Story 2 - Central Repository Schema Baseline & Migrations (Priority: P1)

As a backend engineer, I want an initialized SQLAlchemy 2.x persistence layer and Alembic migration framework targeting PostgreSQL, so that the central catalog schema baseline can be applied, upgraded, and rolled back in a repeatable, version-controlled manner.

**Why this priority**: The central PostgreSQL database is the system of record for all catalog identity, metadata, history, and audit data (Constitution Principle 8). The migration framework must be established before any persistent entities are introduced.

**Independent Test**: Can be tested independently by running Alembic upgrade to head against an empty PostgreSQL database, inspecting the created schema version table, running downgrade to base, and confirming clean rollback without leftover artifacts.

**Acceptance Scenarios**:

1. **Given** a running PostgreSQL instance, **When** the developer executes the Alembic upgrade command, **Then** the baseline application schema is created and Alembic records the current revision in the database.
2. **Given** a database at the baseline revision, **When** the developer executes an Alembic downgrade command, **Then** the database safely reverts to base without errors.

---

### User Story 3 - Background Task Execution Foundation (Priority: P1)

As a backend engineer, I want an initialized Celery worker connected to Redis with a verifiable baseline health task, so that background asynchronous job execution, progress reporting, and result handling are proven operational for future metadata discovery tasks.

**Why this priority**: Background extraction and reliable asynchronous processing are mandatory architectural requirements (Constitution Principle 7). The broker, worker, and task lifecycle must be proven before implementing long-running discovery logic.

**Independent Test**: Can be tested independently by starting the Celery worker process, submitting a baseline asynchronous ping/verification task through the FastAPI service, and verifying that the task transitions from pending to succeeded with its result retrieved from Redis.

**Acceptance Scenarios**:

1. **Given** Redis and the Celery worker are running, **When** a baseline verification task is triggered, **Then** the worker consumes the task, executes it, and stores the completed state in Redis within 2 seconds.
2. **Given** Redis is unreachable, **When** a background task is dispatched, **Then** the system fails cleanly with a sanitized diagnostic log and does not crash the API process.

---

### User Story 4 - Operator Health & Readiness Probes (Priority: P2)

As a DevOps engineer or orchestrator, I want distinct liveness (`/health/live`) and readiness (`/health/ready`) HTTP endpoints, so that container orchestration and operational monitoring can accurately distinguish between process responsiveness and dependency health.

**Why this priority**: Operational observability and separate liveness/readiness semantics are required by Constitution Principle 9 and AGENTS.md Section 11 to avoid routing requests to unready services.

**Independent Test**: Can be tested independently by issuing HTTP GET requests to `/health/live` (expecting HTTP 200 while process runs) and `/health/ready` (expecting HTTP 200 when PostgreSQL and Redis are connected, and HTTP 503 when either is stopped).

**Acceptance Scenarios**:

1. **Given** the FastAPI backend is running and both PostgreSQL and Redis are reachable, **When** an HTTP GET is sent to `/health/ready`, **Then** the response is HTTP 200 with JSON detailing `{"status": "healthy", "postgres": "connected", "redis": "connected"}`.
2. **Given** PostgreSQL is stopped while the backend is running, **When** an HTTP GET is sent to `/health/ready`, **Then** the response is HTTP 503 with JSON detailing `{"status": "unhealthy", "postgres": "disconnected"}` while `/health/live` continues to return HTTP 200.

---

### User Story 5 - Automated Quality Gates & Verification Foundations (Priority: P2)

As a software engineer, I want automated linting, type-checking, and test runner configurations for both backend and frontend, so that all code quality gates can be executed locally and in CI in an offline environment without external network calls.

**Why this priority**: Testing and strict quality gates are mandatory under Constitution Principle 11. Tooling must enforce code consistency, type safety, and determinism from day one.

**Independent Test**: Can be tested independently by executing the root verification script or individual test commands in an environment with outbound internet access disabled, verifying that all lint, type, and unit checks pass.

**Acceptance Scenarios**:

1. **Given** the monorepo codebase, **When** the developer runs the backend test suite, **Then** pytest executes unit tests and reports 100% pass rate in under 10 seconds without making network requests.
2. **Given** the monorepo codebase, **When** the developer runs frontend linting and type-checking, **Then** strict TypeScript checks and ESLint rules execute and report zero errors.

---

### User Story 6 - Developer Setup & Architecture Guidance Documentation (Priority: P3)

As a contributor, I want clear onboarding documentation in `docs/dev-setup.md` and sanitized environment configuration templates, so that I can configure my local workstation and understand architecture boundaries without guesswork.

**Why this priority**: Predictable onboarding eliminates setup friction and ensures every developer adheres to monorepo boundaries and security policies.

**Independent Test**: Can be tested independently by having a new engineer follow `docs/dev-setup.md` step-by-step to achieve a working development environment.

**Acceptance Scenarios**:

1. **Given** a developer following `docs/dev-setup.md`, **When** they copy `.env.example` to `.env`, **Then** every required configuration key is clearly described with sensible local defaults and zero plaintext secrets.

---

### Edge Cases

- **PostgreSQL Unavailable at Startup**: When the backend starts up before PostgreSQL is ready, the application must not crash; it must report degraded/unhealthy status on `/health/ready` and retry connections gracefully.
- **Redis Broker Partition**: If the Redis broker disconnects while background tasks are queued or running, the API must return a controlled service error for new job submissions and log structured diagnostics with a correlation ID.
- **Alembic Schema Drift**: If local database state diverges from Alembic migration history, migration commands must fail with a descriptive error rather than applying partial destructive changes.
- **Offline Dependency Execution**: If a developer or CI environment runs tests or builds with public internet access disabled, no package manager or test runner may fail due to attempted external network fetches.
- **Malformed Configuration**: If `.env` contains invalid data types or missing required values, the Pydantic Settings layer must raise a clear, fail-fast configuration error during process startup.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Monorepo MUST follow the strict directory structure defined in Constitution Principle 2: `/backend`, `/frontend`, `/infrastructure`, `/docs`, and `/scripts`.
- **FR-002**: Backend MUST be implemented with Python and FastAPI, using thin HTTP routers that delegate business logic to application services.
- **FR-003**: Configuration management MUST use centralized Pydantic Settings, loading from environment variables and `.env` files with strict type validation.
- **FR-004**: The project MUST provide a sanitized `.env.example` in `/backend` (and root if applicable) documenting all configuration keys with safe local defaults and zero committed secrets.
- **FR-005**: Persistence layer MUST use SQLAlchemy 2.x with typed declarative mappings and an isolated session dependency.
- **FR-006**: Central database migrations MUST be managed via Alembic, initialized with a single PostgreSQL schema baseline revision and bidirectional upgrade/downgrade support.
- **FR-007**: Asynchronous background infrastructure MUST use Celery with Redis configured as both broker and result backend.
- **FR-008**: Backend MUST define a baseline verification task in Celery to validate worker execution, message roundtrips, and result retrieval.
- **FR-009**: Backend MUST expose a liveness endpoint `GET /health/live` returning HTTP 200 and process status whenever the FastAPI process is responsive.
- **FR-010**: Backend MUST expose a readiness endpoint `GET /health/ready` that verifies live database and Redis connectivity, returning HTTP 200 with structured component statuses when healthy, or HTTP 503 when any dependency is unavailable.
- **FR-011**: Frontend MUST be initialized as an Angular 22 Single Page Application using Standalone Components, Signals, strict TypeScript mode, and strict template checking.
- **FR-012**: Frontend MUST integrate PrimeNG and Tailwind CSS 4 using CSS-first configuration (`@import "tailwindcss";`), and MUST NOT include or depend on `ngbase` or `../base/angularbase`.
- **FR-013**: Frontend MUST include a base shell layout and health-check status dashboard view that displays the live backend readiness state.
- **FR-014**: Local development infrastructure MUST provide a Docker Compose configuration in `/infrastructure` defining PostgreSQL 16+ and Redis 7+ services with persistent data volumes and container health checks.
- **FR-015**: Local development workflow MUST operate in Hybrid mode: PostgreSQL and Redis run containerized via Docker Compose, while the FastAPI backend and Angular frontend run natively on the developer's Windows host for interactive debugging and fast live reloading. Documentation in `docs/dev-setup.md` MUST detail all required host prerequisites and execution commands.
- **FR-016**: Backend runtime baseline MUST be pinned to Python 3.12 consistently across developer setup documentation, virtual environment configuration, tooling configurations (`pyproject.toml`, `.python-version`), and Dockerfiles.
- **FR-017**: Frontend MUST implement an initial application shell featuring bidirectional (RTL/LTR) layout support, PrimeNG provider configuration, and a Tailwind CSS 4 theme baseline, establishing the localization foundation without introducing catalog business features.
- **FR-018**: Backend MUST include a testing foundation using `pytest` with fixtures for database sessions, Redis mock/test instances, and FastAPI `TestClient`.
- **FR-019**: Backend MUST configure Ruff for code linting and formatting, and Mypy for static type checking, enforcing strict typing and style without redundant linters.
- **FR-020**: Frontend MUST include unit testing configuration and ESLint rules enforcing strict TypeScript and component standards.
- **FR-021**: Documentation in `docs/dev-setup.md` MUST provide end-to-end instructions for local workspace initialization, dependency installation, database migration execution, and application verification.

### Non-Functional Requirements

- **NFR-001 (On-Premises / Offline Independence)**: Build, test, and runtime operations MUST NOT require public internet access, public CDNs, or external hosted services (Constitution Principle 1). All frontend assets, fonts, and dependencies must be locally bundled or served from internal infrastructure.
- **NFR-002 (Security & Least Privilege)**: Secrets, passwords, and private keys MUST NOT be committed to version control or hard-coded into defaults. Configuration MUST fail fast on invalid or insecure settings.
- **NFR-003 (Architecture Boundaries)**: HTTP routers MUST remain thin and handle only request parsing, dependency injection, and response formatting. Domain logic and persistence MUST reside in service and repository layers respectively.
- **NFR-004 (Performance & Responsiveness)**: Health endpoints MUST respond in under 50ms under local conditions. Local service startup time for backend and frontend MUST complete in under 5 seconds.
- **NFR-005 (Reliability & Observability)**: Structured logging with standardized levels (INFO, WARNING, ERROR) and request/correlation IDs MUST be established across FastAPI and Celery.
- **NFR-006 (Extensibility & Clean Slate)**: The foundation MUST NOT include any temporary workarounds or dead code for deferred features (authentication, connectors, extraction).

### Key Entities

- **HealthStatus**: Represents the overall application readiness state, comprising service status (`healthy`, `degraded`, `unhealthy`), timestamp (UTC ISO 8601), and a dictionary of dependency statuses (`postgres`, `redis`).
- **ComponentCheckResult**: Represents the individual status of a monitored infrastructure dependency, including component name, connection state (`connected`, `disconnected`), latency milliseconds, and optional sanitized error description.
- **ApplicationConfig**: Encapsulates centralized settings (application name, environment designation, API prefix, CORS origins, PostgreSQL URL, Redis URL, Celery broker URL, logging level).
- **BackgroundTaskRecord**: Encapsulates Celery task execution metadata for verification (task ID, task name, status, start time, completion time, result payload).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can bootstrap the local environment and verify both frontend and backend running successfully in under 15 minutes by following `docs/dev-setup.md`.
- **SC-002**: 100% of automated unit tests, liveness/readiness tests, and lint/type checks pass out of the box in an isolated environment without public internet access.
- **SC-003**: The readiness probe endpoint (`/health/ready`) returns accurate status within 50ms and correctly detects the intentional disconnect of PostgreSQL or Redis within 2 seconds.
- **SC-004**: Database migration commands (`alembic upgrade head` and `alembic downgrade -1`) execute idempotently without errors on a clean database instance.
- **SC-005**: A baseline asynchronous Celery task dispatches, executes, and returns its result to Redis in under 2 seconds.

## Assumptions

### Technical Assumptions
- Developers have Docker (v24+) and Docker Compose (v2+), Node.js (v20+ or v22+ LTS), and Python 3.12 installed on their local Windows workstations.
- Local developer workflow follows Hybrid mode (PostgreSQL and Redis in Docker Compose; FastAPI and Angular running natively on the host).
- Central metadata repository uses PostgreSQL 16+.
- Background task broker and cache use Redis 7+.
- Frontend application is developed strictly as a client-rendered SPA; SSR, SSG, and hydration are completely out of scope per Constitution Principle 10.
- All dependencies can be fetched from local package caches, pre-installed vendor wheels, or internal mirror registries.

### Scope Boundaries & Strict Exclusions
In accordance with the project instructions, the following capabilities are **strictly excluded** from this foundation feature:
1. **No Authentication**: No login forms, password hashing, session tokens, or JWT handling.
2. **No RBAC or Authorization**: No role definitions, permission checking, or category scopes.
3. **No Database Connectors**: No adapters or drivers for SQL Server, MySQL, Oracle, PostgreSQL source discovery, or MongoDB.
4. **No Metadata Extraction**: No discovery jobs, table inspection, schema diffing, or sampling logic.
5. **No Data Catalog Business Features**: No dataset listing, category management, search interfaces, or governance workflows.
6. **No AI Integration**: No AI endpoints, LLM calls, or metadata enrichment hooks (Constitution Principle 13).

