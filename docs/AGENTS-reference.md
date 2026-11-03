# AGENTS.md — Enterprise Data Catalog Development Guidelines

> This file is the authoritative project-specific instruction set for AI coding agents and contributors. Apply it together with the feature specification, architecture decisions, security policies, and approved API contracts. If instructions conflict, security and data-protection requirements take precedence; then follow the approved project specification and architecture decisions. Do not silently invent requirements.

## 1. Project Mission and Fixed Technology Stack

Build an on-premises Enterprise Data Catalog for discovering, describing, organizing, searching, governing, and auditing metadata across organizational data sources.

### 1.1 Project scale and operating assumptions

- Initial scope includes approximately 700 database instances and an average of approximately 200 relational tables per database (about 140,000 tables overall). Treat these as planning estimates, not hard-coded limits.
- Expected user population is approximately 600 users.
- The application is deployed inside the organization's infrastructure. Runtime operation must not depend on public internet access.
- Initial authentication is local username/password authentication. Active Directory/LDAP/SSO integration is not part of the initial release unless separately approved.
- AI-assisted metadata enrichment is a future capability, not an enabled initial-release dependency. Design extension points, but do not send metadata to external AI services or add AI credentials without explicit security and product approval.

### 1.2 Technology stack

| Area | Required technology |
|---|---|
| Frontend | Angular 22, Standalone Components, Signals, TypeScript strict mode |
| UI | PrimeNG and Tailwind CSS 4; no `ngbase` |
| Backend | Python with FastAPI |
| API schemas and validation | Pydantic |
| ORM / persistence | SQLAlchemy 2.x |
| Database migrations | Alembic |
| Central repository | PostgreSQL |
| Background processing | Celery |
| Broker / cache | Redis |
| Relational connectors | SQL Server, MySQL, Oracle, PostgreSQL |
| Document database connector | MongoDB |
| Reverse proxy / TLS termination | Nginx or an organization-approved equivalent |
| Authentication password hashing | Argon2id |

Use supported stable releases that are mutually compatible. Do not arbitrarily upgrade major versions or pin an unverified “latest” version. Record exact versions in lockfiles and deployment manifests after compatibility has been verified.

### 1.3 Repository layout

Use a monorepo with strict separation:

```text
project-root/
├── backend/
├── frontend/
├── infrastructure/
├── docs/
├── scripts/
├── .gitignore
└── README.md
```

- Backend Python code and dependencies belong only under `/backend`.
- Angular code, assets, and Node dependencies belong only under `/frontend`.
- Deployment configuration belongs under `/infrastructure`.
- Architecture decisions, API contracts, operational guides, and user/developer documentation belong under `/docs`.
- Never mix Java/Spring/Gradle artifacts into this project. This project uses Python/FastAPI, not Java/Spring Boot.

## 2. Environment, Configuration, and Repository Hygiene

### 2.1 Secrets and environment configuration

- Never commit passwords, API keys, database connection strings containing credentials, private keys, tokens, or production secrets.
- Load backend configuration from environment variables using a centralized Pydantic Settings configuration layer.
- Provide a sanitized `.env.example`; never commit a populated `.env` file.
- Separate development, test, staging, and production configuration without duplicating application logic.
- Frontend environment files may contain public configuration such as the API base path, but must never contain secrets.
- Prefer a same-origin reverse-proxy API path in deployed environments where practical. Never hard-code hostnames, ports, or environment-specific API URLs in components or services.

### 2.2 Git and ignore rules

The root `.gitignore` must exclude, at minimum:

- Python virtual environments, `__pycache__`, `.pytest_cache`, coverage output, build artifacts, and local environment files.
- Node dependencies, Angular build/cache output, and local tool caches.
- Logs, temporary extraction exports, generated credentials, local database dumps, and IDE/OS files.
- Any file containing source database credentials or extracted business data.

Track exactly one frontend package-manager lockfile. Use the package manager already established by the repository; if the repository has no choice, use npm by default. Do not mix npm and Yarn lockfiles.

### 2.3 Dependency discipline

- Do not add a third-party dependency without a concrete need and review of maintenance, license, security, compatibility, and on-premises installation implications.
- All required runtime packages, frontend assets, fonts, and browser libraries must be installable and available from approved internal mirrors or bundled artifacts.
- No runtime dependency on public CDNs or external internet services.
- Development tools may access the internet only where organizational policy permits. Production runtime must remain functional without outbound internet.

## 3. Backend Architecture — FastAPI

### 3.1 Layering and boundaries

Use a modular layered architecture:

```text
HTTP Router -> Application / Domain Service -> Repository -> PostgreSQL
                                  |
                                  +-> Connector / Metadata Extraction Services
                                  +-> Background Job Services (Celery)
```

Suggested backend layout (adapt names only when the existing codebase has a sound convention):

```text
backend/
├── app/
│   ├── api/                 # FastAPI routers and dependency wiring
│   ├── core/                # Settings, security, logging, shared policies
│   ├── schemas/             # Pydantic request/response schemas
│   ├── models/              # SQLAlchemy models
│   ├── repositories/        # Database persistence queries
│   ├── services/            # Use cases and domain orchestration
│   ├── connectors/          # SQL Server, MySQL, Oracle, PostgreSQL, MongoDB
│   ├── extraction/          # Metadata discovery, normalization, diffing
│   ├── jobs/                # Celery tasks and scheduling integration
│   ├── audit/               # Audit event creation and query services
│   └── main.py
├── migrations/              # Alembic environment and revisions
├── tests/
├── pyproject.toml
└── alembic.ini
```

- Routers handle HTTP concerns only: parsing, authentication/authorization dependencies, status codes, and response serialization.
- Services implement use cases and business rules. Do not put business logic in routers or ORM model event hooks without a clear reason.
- Repositories encapsulate persistence queries. Do not expose SQLAlchemy sessions or ORM entities directly to the frontend.
- Connector code must be isolated from the central repository and must not make the API layer depend on a specific vendor driver.
- Use dependency injection for database sessions, authenticated principals, configuration, and service dependencies.

### 3.2 Pydantic schemas and API contracts

- Pydantic schemas are mandatory for request validation and response contracts. Do not follow the old source file's “NO DTOs” rule; that rule belongs to a different Java/Spring application and is invalid here.
- Keep request, response, and persistence models distinct where their responsibilities differ.
- Never serialize SQLAlchemy entities blindly. Explicitly select fields returned by each API endpoint.
- Do not expose password hashes, encrypted connection secrets, internal tokens, raw driver errors, or fields the caller is not authorized to see.
- Use consistent pagination, filtering, sorting, validation, and error-response conventions across endpoints.
- Version public API contracts deliberately. Document breaking changes and update frontend types and tests together.

### 3.3 Error handling

- Use centralized FastAPI exception handlers and a consistent error response shape.
- Distinguish validation errors, authentication failures, authorization failures, missing resources, conflicts, connector failures, extraction failures, and unexpected internal errors.
- Return safe client messages. Keep stack traces, credentials, connection strings, SQL text containing sensitive values, and vendor-specific secrets out of API responses.
- Preserve diagnostic context in protected server logs using a request/correlation ID.

### 3.4 Asynchronous work

- Long-running metadata extraction, large scans, and scheduled discovery must run as background jobs; do not hold an HTTP request open for a full extraction.
- Use Celery workers with Redis as broker/backend according to the approved deployment topology.
- Track job type, target source, requested-by user, lifecycle state, progress where meaningful, start/end timestamps, retry count, and sanitized error details.
- Implement bounded retries with backoff for transient failures. Do not retry permanent authentication, permission, or configuration failures indefinitely.
- Prevent overlapping extraction jobs for the same source/scope unless explicitly supported.
- Enforce worker concurrency, per-source connection limits, and global resource limits. Avoid exhausting source databases or the central repository.
- Make tasks idempotent where feasible. A retry must not duplicate metadata or corrupt inventory state.
- Use Celery Beat or an approved scheduler for recurring extraction. Store schedule configuration and execution history centrally.

## 4. Central Repository and Database Design

### 4.1 PostgreSQL is the catalog repository

PostgreSQL stores the Data Catalog application's own data, including:

- Users, roles, permissions, sessions/tokens as applicable, and authentication audit events.
- Hierarchical categories and category-to-source relationships.
- Registered data sources and encrypted connection configuration.
- Extracted metadata for relational databases and MongoDB.
- Metadata descriptions, ownership, tags, classifications, and version history.
- Extraction jobs, schedules, execution results, and schema-change observations.
- Audit events and operational configuration.

The organization's source databases are read-only discovery targets by default. Do not confuse source databases with the central PostgreSQL repository.

### 4.2 PostgreSQL schema strategy — recommended, not dogmatic

- Start with one application schema (normally `public` or one explicitly named application schema) for the initial release. This keeps migrations, operations, and cross-domain queries straightforward.
- Organize domains logically through table naming, constraints, indexes, SQLAlchemy model modules, and repository/service boundaries; do not create schemas merely to mirror Python packages.
- Do not impose an unconditional “single schema forever” rule. Multiple schemas may be introduced only when a documented requirement justifies them, such as strong database-level privilege isolation, independent ownership/lifecycle, or a measured operational need.
- Any move to multiple schemas requires an architecture decision record (ADR), migration/rollback plan, privilege model, and test coverage before implementation.
- Never create a schema per registered source database or per end user as a default strategy.

### 4.3 SQLAlchemy and Alembic

- Use SQLAlchemy 2.x typed declarative mappings and explicit transaction boundaries.
- Use Alembic for every persistent schema change. Never modify a deployed database manually as a substitute for a migration.
- Review generated migrations before applying them. Autogenerated migrations are drafts, not guaranteed-correct output.
- Each migration must have a clear purpose, deterministic revision chain, and upgrade/downgrade behavior where downgrade is safe and meaningful.
- Avoid destructive changes without explicit data-impact analysis, backup/restore plan, and approval.
- Use UUID identifiers for application entities by default. Choose other key types only when justified by data volume, indexing, interoperability, or a documented domain requirement.
- Use timezone-aware timestamps and a consistent UTC storage policy.
- Add indexes based on real access patterns. Validate expensive queries with representative data and query plans.
- Use JSONB only for genuinely flexible metadata payloads; keep frequently filtered/joined attributes in typed relational columns.

### 4.4 Naming and audit fields

- Use `snake_case` for PostgreSQL table and column names.
- Use explicit foreign keys, uniqueness constraints, check constraints, and deletion policies.
- Standard operational entities should carry appropriate creation/update timestamps and actor references where meaningful.
- Do not treat generic `created_at`/`updated_at` columns as a replacement for the dedicated immutable audit-event log described below.

## 5. Data Catalog Domain Requirements

### 5.1 Supported source types and connector contract

The initial connector set must support:

- Microsoft SQL Server
- MySQL
- Oracle Database
- PostgreSQL
- MongoDB

Define a common connector contract for connection validation, capability discovery, metadata extraction, health checks, and sanitized error reporting. Vendor-specific behavior belongs inside its connector adapter.

- Use read-only source credentials wherever the source platform supports them.
- Validate connection settings before saving or scheduling extraction.
- Never allow a connector to execute arbitrary user-provided SQL or commands as part of ordinary metadata discovery.
- Apply connection timeouts, query timeouts, bounded retries, and per-source concurrency limits.
- Support TLS and certificate validation when configured by the source system. Do not silently disable certificate verification to “make a connection work.”
- Do not extract business records by default. The initial scope is structural metadata. Any sampling or profiling must be an explicit, separately authorized feature with row limits, masking, and audit controls.

### 5.2 Relational metadata

Discover and represent, as supported by each vendor:

- Server/instance and database identity.
- Schemas, tables, views, columns, data types, nullability, defaults, primary keys, foreign keys, unique constraints, indexes, and relationships.
- Table/column comments and source-provided descriptions.
- Vendor-specific attributes only where useful and documented.

Normalize common concepts across vendors without discarding original vendor type names or source-specific details. Record extraction time and source identity for discovered metadata.

### 5.3 MongoDB metadata is document-oriented

Do not force MongoDB into a relational table/column model.

Represent MongoDB-specific concepts such as database, collection, document structure, nested field paths, arrays, observed BSON types, optional/mixed types, and sampling/profiling provenance where enabled. Preserve the distinction between observed structure and guaranteed schema: MongoDB collections may contain heterogeneous documents and fields may be absent.

Any sampling must be bounded, configurable, read-only, and clearly marked as sampled/observed rather than complete. Never imply that a sample proves the entire collection's schema.

### 5.4 Metadata identity, change detection, and history

- Use stable source-scoped identifiers for metadata objects where the source provides them; otherwise define deterministic identity rules and document their limitations.
- Detect additions, removals, and changes to discovered objects and attributes.
- Preserve extraction snapshots or equivalent history sufficient to explain schema evolution.
- Do not silently overwrite user-authored descriptions when source metadata changes.
- Keep source-provided description, user-authored description, and future AI suggestions as separate values/provenance.
- Version description changes with author, timestamp, status, and approval information where workflow requires it.
- Treat AI-generated suggestions as untrusted proposals requiring human review and approval before becoming authoritative metadata.

### 5.5 Source registration and categorization

- Administrators can define a hierarchical category tree and register sources under appropriate categories.
- A source must have an explicit lifecycle/status and a controlled ownership model.
- Category hierarchy must support parent/child relationships and the approved access-inheritance behavior.
- Do not expose connection secrets in source detail APIs, logs, exports, or frontend state.

### 5.6 Search

- Implement catalog search against central metadata, not by querying all source databases interactively for each user search.
- Use PostgreSQL Full Text Search and `pg_trgm` where they fit language, fuzzy matching, and workload requirements.
- Search results must be filtered by effective user permissions before they are returned. Do not rely on frontend filtering for confidentiality.
- Provide pagination and bounded result sizes. Avoid unbounded metadata responses.
- Measure and tune search with representative catalog volume and realistic concurrent usage.

## 6. Authentication, Authorization, and Security

### 6.1 Local authentication

- Implement local authentication for the initial release.
- Hash passwords using Argon2id with maintained library defaults or parameters reviewed against current security guidance.
- Never store plaintext passwords or reversible password encryption.
- Apply secure session/token handling, expiration, revocation, and CSRF protection where applicable to the chosen authentication transport.
- Rate-limit authentication attempts and protect against account enumeration.
- Implement configurable temporary account lockout or progressive delays after repeated failed authentication attempts. Design recovery and administrative controls to reduce denial-of-service abuse. Do not invent a universal lockout threshold; make policy configurable and security-reviewed.
- Record account lockout, unlock, and administrative recovery events in the audit log.
- Provide a secure backend-enforced mechanism for users to revoke all of their active sessions.
- Allow authorized administrators to revoke all active sessions for a user when required; audit the action.
- Password changes, account deactivation, and security-sensitive account changes must invalidate existing sessions according to the approved security policy. Revocation must not rely solely on deleting browser-side tokens or cookies.
- Do not add AD/LDAP/SSO integration until separately approved and specified.

### 6.2 RBAC and category inheritance

- Use role-based access control with explicit permissions and resource/category scope.
- Users may have multiple roles. Effective permissions are computed from all active role assignments and applicable scope rules.
- Support category-level access and source-level access according to the approved authorization model.
- Category access inheritance must be explicit and testable. The initial design uses inherited access from parent categories to descendants unless an approved rule defines an exception.
- Enforce authorization in backend services/dependencies for every protected operation. Hiding a menu item or button is not authorization.
- Deny by default. A missing or ambiguous permission must not grant access.
- Administrators must be able to inspect role membership and effective access without exposing secrets.
- Record changes to users, roles, role assignments, permissions, and category/source access in the audit log.

### 6.3 Connection secret protection

- Encrypt stored source credentials using an approved encryption-at-rest design with keys kept outside the database and source repository.
- Prefer an organization-approved secret manager or key-management service. If unavailable, document key custody, rotation, backup, and recovery before implementing application-managed encryption.
- Never log decrypted credentials or return them from an API after initial submission.
- Restrict decryption to the narrow backend component that needs to establish a source connection.
- Support credential rotation and connection revalidation without exposing old secrets.

### 6.4 Audit logging

Record security- and governance-relevant events, including as applicable:

- Successful and failed login/logout events.
- User, role, role assignment, permission, category, and source changes.
- Connection configuration changes and credential rotation events (never the secret itself).
- Extraction requests, schedule changes, job outcomes, and privileged administrative actions.
- Metadata description, ownership, classification, and approval changes.

Audit events should include actor, action, entity type/id, timestamp, outcome, request/correlation ID, and source context such as IP where policy permits. Capture before/after values selectively, redact secrets and sensitive payloads, and restrict audit-log access. Ordinary application users must not be able to modify or delete audit history.

### 6.5 General application security

- Validate all inputs at trust boundaries.
- Use parameterized ORM queries; avoid unsafe SQL string concatenation.
- Apply least privilege to application database accounts, worker accounts, and source credentials.
- Configure TLS for browser-to-proxy and service-to-service paths according to deployment policy.
- Set secure HTTP headers and a restrictive Content Security Policy compatible with the application.
- Protect against common web risks including injection, broken access control, XSS, CSRF, SSRF, insecure deserialization, and unsafe file handling.
- Do not let users supply arbitrary connector hosts without network/egress controls. Protect connector functionality against SSRF and access to infrastructure metadata endpoints.
- Keep dependencies patched and run vulnerability/dependency checks as part of CI.

## 7. Frontend Architecture — Angular 22

### 7.1 Rendering decision

- **SSR is explicitly disabled.** Build and deploy the Angular application as a client-rendered SPA.
- Do not add Angular SSR, SSG/prerendering, server routes, hydration, event replay, or browser/server rendering compatibility code unless a new architecture decision explicitly changes this choice.
- Do not add SEO/GEO, public sitemap, crawler-oriented metadata, or public structured-data infrastructure for authenticated internal catalog screens. If a public-facing site is introduced later, assess it separately.

### 7.2 Angular standards

- Use Standalone Components and modern Angular APIs (Signals where appropriate).
- Use `inject()` for dependency injection where it improves clarity and consistency.
- Enable TypeScript strictness and strict Angular template checking.
- Use typed Reactive Forms for complex forms and validation.
- Keep components focused on presentation and interaction. Put API communication and reusable business behavior in services/facades.
- Lazy-load feature routes and avoid loading large feature areas before they are needed.
- Do not use `any` except for a narrowly justified interoperability boundary with an explanatory comment and safe narrowing.
- Maintain explicit frontend models/contracts aligned with API schemas. Do not assume a frontend interface replaces backend validation.

### 7.3 Component file structure

Use separate `.ts`, `.html`, and `.scss` files as the default for feature and reusable components. A narrowly scoped inline template/style may be used only for genuinely trivial components when it materially improves maintainability; do not turn file separation into pointless boilerplate.

### 7.4 UI libraries and styling

- Use PrimeNG for standard enterprise UI controls, tables, dialogs, trees, menus, and feedback components where appropriate.
- Use Tailwind CSS 4 for layout and utility styling.
- `ngbase` is explicitly not used. Do not inspect for, install, import, or depend on `../base/angularbase` or `node_modules/ngbase`.
- Do not introduce a replacement enterprise UI abstraction without an explicit architecture review.
- Use Tailwind CSS 4 CSS-first configuration (`@import "tailwindcss";` and `@theme` as needed); do not copy Tailwind 3 configuration patterns into a Tailwind 4 project.
- Prefer logical/bidirectional properties for layout: `ms-*`, `me-*`, `ps-*`, `pe-*`, `start-*`, `end-*`, `text-start`, and `text-end`. Avoid physical left/right assumptions where a logical property is available.
- Use custom SCSS for component-specific styling, PrimeNG overrides, and cases not expressed clearly with utilities. Do not force every style into Tailwind.

### 7.5 RTL/LTR and localization

- Support Persian RTL and English LTR layouts.
- Centralize locale and direction state; update the root `lang` and `dir` attributes when the active language changes.
- Verify PrimeNG overlays, tables, calendars, dialogs, menus, icons, and keyboard navigation in both directions.
- Keep user-visible strings out of component logic where a localization resource is appropriate.
- Use locale-aware date, number, and currency formatting. Store timestamps in a consistent backend representation and convert for display.

### 7.6 Frontend API and state handling

- Centralize the API base path in environment configuration or an approved runtime configuration endpoint.
- Use typed Angular services for HTTP access. Do not call APIs directly from templates.
- Handle loading, empty, error, and permission-denied states explicitly.
- Do not store source database passwords, access tokens, or other secrets in browser storage unless the authentication design explicitly requires a secure, reviewed mechanism.
- Do not cache authenticated API responses or catalog metadata in service-worker caches or persistent browser storage by default.

## 8. Offline and Asset Policy

The selected offline scope is **local assets only**.

- Bundle application JavaScript, CSS, icons, and fonts locally. No public CDN dependency.
- The application must load its static assets from the organization's deployment environment without reaching public internet services.
- API data remains server-backed. When the backend is unreachable, show a clear connectivity/service error and provide safe retry behavior.
- Do not implement offline CRUD, queued writes, background synchronization, or conflict resolution in the initial release.
- Do not add PWA service-worker API caching, offline catalog snapshots, or authenticated data caching by default.
- Do not describe the application as fully offline-capable. Only its static assets are locally bundled.
- Use local, licensed fonts and optimized image assets. Avoid downloading assets dynamically from third-party hosts at runtime.

## 9. Testing Strategy — Strict and Mandatory

Testing is mandatory for backend and frontend. The previous source file's instruction to skip unit tests is explicitly rejected.

### 9.1 Backend tests

Use pytest and suitable FastAPI/SQLAlchemy test tooling. Require:

- Unit tests for domain services, permission calculations, metadata normalization, schema diffing, and validation logic.
- API/integration tests for routers, authentication, authorization, persistence, migrations, and error handling.
- Connector contract tests for each supported database type. Use containers, test instances, or controlled fixtures where practical; clearly mark tests requiring external infrastructure.
- Security tests for access-control boundaries, role inheritance, credential redaction, authentication throttling, and unauthorized source access.
- Background-job tests for idempotency, retry policy, duplicate-run prevention, and failure handling.
- Regression tests for every fixed defect.

### 9.2 Frontend tests

Use the Angular project's supported test runner and tooling. Require:

- Unit tests for services, guards, permission-aware UI logic, state transformations, and non-trivial components.
- Component tests for forms, tables, loading/error/empty states, and accessibility-sensitive interactions.
- Integration tests for important user workflows such as source registration, category management, role assignment, and metadata browsing.
- RTL and LTR coverage for shared layout and high-usage components.

### 9.3 Quality gates

- Tests must be deterministic and isolated. Do not rely on production databases or real production credentials.
- CI must run formatting/linting, type checks, backend tests, frontend tests, and production builds.
- Security-sensitive changes require targeted security tests and review.
- Do not reduce or delete test coverage merely to make a build pass. If a test is invalid, replace it with a correct test and explain why.
- Performance tests must use representative data volumes and document the environment and methodology. Do not invent performance guarantees without measurement.

## 10. Performance, Scale, and Reliability

- Design for the stated catalog scale (approximately 140,000 relational tables initially) and approximately 600 users, while allowing future growth.
- Use pagination for large lists and avoid returning entire inventories in one response.
- Use bulk persistence and bounded batches for metadata extraction; avoid one database commit per metadata field/object.
- Tune SQLAlchemy connection pools, worker concurrency, Redis capacity, and source connection limits based on measured load.
- Avoid N+1 ORM queries. Use explicit eager-loading or purpose-built projections where appropriate.
- Add indexes for actual search, filtering, joins, and authorization checks. Validate with query plans and realistic data.
- Ensure extraction jobs can resume or safely retry after partial failure.
- Use health/readiness checks for API, PostgreSQL, Redis, and workers. A healthy API process alone does not prove extraction capability is healthy.
- Provide structured logs and metrics without logging secrets or business data unnecessarily.
- Define backup and restore procedures for the central repository, encryption keys, and job/audit data. Test restoration periodically.

## 11. Observability and Operations

- Use structured application logs with consistent timestamps, severity, service name, and correlation/request IDs.
- Track API errors/latency, database pool health, Redis health, worker queue depth, extraction duration/failure rate, source connectivity, and scheduler execution.
- Separate liveness from readiness checks.
- Ensure operational dashboards and logs do not expose passwords, connection strings, tokens, or sensitive metadata.
- Document installation, upgrade, backup, restore, certificate rotation, secret rotation, and disaster-recovery procedures.
- Deployment must be reproducible in the organization's on-premises environment and must not require public internet access at runtime.

## 12. Documentation and Change Management

- Document each connector's supported metadata capabilities and limitations.
- Maintain API documentation and examples consistent with the implemented FastAPI contracts.
- Record significant architecture decisions as ADRs, including context, decision, alternatives, security impact, and consequences.
- Update docs, tests, migrations, and frontend/backend contracts together when a feature changes.
- Never silently change authorization semantics, metadata identity rules, extraction scope, or credential-handling behavior.
- For destructive or large-scale extraction changes, include impact analysis, rollout strategy, rollback/recovery plan, and operational safeguards.

## 13. Definition of Done

A feature or bug fix is not complete until all applicable items below are satisfied:

1. Acceptance criteria are implemented and reviewed.
2. Backend business rules are in services/domain layers, not hidden in routers or frontend code.
3. Request and response contracts use explicit Pydantic schemas; sensitive fields are excluded.
4. Authorization is enforced server-side for every protected operation and tested for both allowed and denied cases.
5. Database changes are represented by reviewed Alembic migrations.
6. Connector operations are read-only by default, bounded, timeout-protected, and do not log secrets.
7. Background jobs have clear state transitions, retry limits, and duplicate-run protection where applicable.
8. Audit events are recorded for applicable security/governance changes, with secrets redacted.
9. Unit, integration, security, and regression tests appropriate to the change pass.
10. Frontend works in both RTL and LTR where the affected UI is shared/localized.
11. Loading, empty, error, and unauthorized states are handled.
12. Static assets are local; no runtime CDN or public internet dependency is introduced.
13. No SSR/SSG/hydration/PWA API caching has been added without an approved architecture change.
14. Formatting, linting, type checking, tests, and production builds pass.
15. Documentation and operational instructions are updated.
16. No secrets, production data, generated dumps, or local environment files are committed.

## 14. Prohibited Patterns

- Do not use Java, Spring Boot, Spring Data JPA, QueryDSL, Gradle, Lombok, Liquibase, or Java-specific annotations in this project.
- Do not bypass Pydantic request/response schemas by exposing ORM entities directly.
- Do not put business rules or authorization decisions only in Angular.
- Do not assume category visibility in the UI is sufficient access control.
- Do not store source credentials in plaintext or log them.
- Do not extract source business rows as part of ordinary metadata discovery.
- Do not model MongoDB collections as if they had a guaranteed relational schema.
- Do not run unbounded extraction, sampling, search, or API queries.
- Do not create SSR, SSG, prerendering, hydration, or server-rendering infrastructure in the initial SPA architecture.
- Do not implement offline data caching, offline writes, or background sync in the initial asset-only offline scope.
- Do not use `ngbase` or depend on the legacy `../base` library.
- Do not disable, skip, or omit tests. Backend and frontend tests are mandatory.
- Do not create multiple PostgreSQL schemas without a documented ADR and approved need.
- Do not introduce dependencies, external services, or outbound network calls without review.
- Do not hard-code environment-specific API URLs or secrets in source code.

## 15. Technology and Architecture Decision Register

The following decisions are confirmed for the initial project baseline:

| Decision | Selected value |
|---|---|
| Repository | Monorepo with separate backend/frontend directories |
| Backend | Python + FastAPI |
| Frontend | Angular 22 SPA |
| ORM | SQLAlchemy 2.x |
| Migration | Alembic |
| Central database | PostgreSQL |
| Schema strategy | Start with one schema; allow multiple only with documented justification and ADR |
| Background jobs | Celery + Redis |
| Authentication | Local authentication initially |
| Password hashing | Argon2id |
| SSR | No |
| Offline | Local static assets only; API remains online/server-backed |
| UI libraries | PrimeNG + Tailwind CSS 4 |
| ngbase | No |
| Tests | Strict; unit, integration, security, and relevant performance tests mandatory |
| AI | Future capability; disabled until approved |
| Deployment | On-premises; runtime must not require public internet |

Technology versions must be checked for compatibility at implementation time and recorded in the project's lockfiles and deployment documentation. This document intentionally avoids unsupported or contradictory version claims.
