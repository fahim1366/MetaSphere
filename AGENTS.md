# AGENTS.md — Data Catalog Project Instructions

This file is the always-on, concise project rule set. Before planning, editing, generating, or reviewing code, the agent MUST read `docs/AGENTS-reference.md` in full and follow its detailed requirements. The detailed reference is part of the project instructions, not optional background reading.

If the reference and this file appear to conflict, stop and report the conflict. Do not silently choose. The Constitution at `.specify/memory/constitution.md` defines non-negotiable principles; approved security policy and ADRs take precedence as defined in that document.

## 1. Product and operating constraints

- Build an on-premises Enterprise Data Catalog for discovering, describing, organizing, searching, governing, and auditing metadata across heterogeneous data sources.
- Initial planning assumptions: about 700 database instances, about 200 relational tables per instance (about 140,000 tables), and about 600 users. These are capacity-planning assumptions, not hard-coded limits or performance guarantees.
- Production runtime must not depend on public internet, public CDNs, externally hosted fonts, unapproved telemetry, or unapproved third-party services.
- The catalog is metadata-first. Do not copy business rows during ordinary discovery.
- AI integration and transmission of metadata to AI services are disabled unless separately approved by product, security, and organizational authorities.

## 2. Approved technology stack

- Frontend: Angular 22, Standalone Components, strict TypeScript, PrimeNG, Tailwind CSS 4.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic.
- Central repository: PostgreSQL; background processing: Celery + Redis.
- Reverse proxy/TLS: Nginx or an organization-approved equivalent.
- Initial authentication: local username/password with Argon2id. AD/LDAP/SSO are out of scope unless separately approved.
- Supported initial connectors: SQL Server, MySQL, Oracle, PostgreSQL, MongoDB.
- Use compatible supported versions and lockfiles. Do not assume “latest” is compatible.
- Do not introduce Java, Spring Boot, JPA, QueryDSL, Gradle, Lombok, Liquibase, or `ngbase`.

## 3. Architecture and repository boundaries

Use a monorepo with `/backend`, `/frontend`, `/infrastructure`, `/docs`, and `/scripts`.

- Keep HTTP routers thin. Put business rules in domain/application services and persistence queries in repositories.
- Keep connectors behind a documented common contract; isolate vendor-specific drivers and behavior.
- Frontend components handle presentation and interaction; services/facades own API access and reusable behavior.
- Frontend must not make authoritative business-rule or authorization decisions.
- Use explicit Pydantic request/response contracts. Never expose SQLAlchemy entities or sensitive fields directly.
- Search and browse the central metadata repository; do not fan out to all source databases for each user search.

## 4. Data discovery and metadata correctness

- Treat source databases as read-only discovery targets by default. Use least-privilege credentials.
- Do not extract business rows during ordinary discovery. Any future sampling/profiling requires separate approval, bounded limits, safeguards, and auditability.
- Preserve vendor type names and relevant source-specific attributes when normalization would lose meaning.
- Model MongoDB using document concepts: databases, collections, nested field paths, arrays, observed BSON types, optional/mixed fields. Mark sampled observations as observations, not guaranteed complete schemas.
- Keep source descriptions, user-authored descriptions, and future AI suggestions distinct with provenance. Never silently overwrite user-authored descriptions.
- Detect and record added, changed, and removed metadata objects with deterministic, source-scoped identity where possible.

## 5. Security and authorization

- Hash user passwords with Argon2id; never store plaintext or reversibly encrypted passwords.
- Encrypt source credentials at rest. Keep encryption keys outside the database and source repository. Never expose secrets in APIs, frontend state, logs, exceptions, screenshots, or commits.
- Support users with multiple roles, explicit permissions, category/source scopes, and documented parent-to-descendant category inheritance.
- Enforce effective permissions in the backend on every protected operation. Deny by default. UI hiding is not security.
- Apply authentication rate limits and account-enumeration protections. Support secure session expiry/revocation, configurable lockout or progressive delays, audited lockout/recovery, user-wide session revocation, and authorized administrator revocation. Security-sensitive account changes must invalidate sessions according to policy.
- Protect source registration against SSRF and unauthorized access to internal endpoints.
- Audit users, roles, permissions, category/source access, source configuration, credential rotation events, extraction, and metadata governance changes. Never log credential values.

## 6. Central database and migrations

- Start with one PostgreSQL application schema. Multiple schemas require an approved ADR, privilege model, migration/rollback plan, and tests.
- Use SQLAlchemy 2.x typed mappings, explicit transaction boundaries, constraints, and measured indexes.
- Every persistent schema change requires a reviewed Alembic migration. Autogenerated migrations are drafts; destructive changes require impact analysis and approval.
- Use timezone-aware timestamps (UTC recommended); UUIDs by default unless a documented reason justifies otherwise.
- Use JSONB for genuinely flexible attributes, not as a substitute for well-designed relational columns.
- Generic created/updated timestamps do not replace dedicated audit history.

## 7. Background extraction and reliability

- Long-running and scheduled extraction must run asynchronously using Celery workers and Redis.
- Persist observable job state: type, source/scope, requester, lifecycle, timestamps, retries, progress where meaningful, and sanitized errors.
- Make tasks safe to retry and prevent duplicate/overlapping runs for the same source/scope unless explicitly supported.
- Use bounded retries with backoff for transient failures; do not endlessly retry permanent authentication/configuration failures.
- Bound worker concurrency, per-source connections, batch sizes, and global resource use.
- Recover partial failures without marking incomplete metadata as successfully refreshed or destroying the last known-good complete inventory.

## 8. Frontend and user experience

- Angular is a client-rendered SPA. No SSR, SSG, prerendering, or hydration without an approved ADR.
- Support Persian RTL and English LTR; prefer CSS logical properties and centrally managed locale/direction.
- Use Standalone Components, strict TypeScript/template checking, typed forms, lazy feature routes, and Signals where appropriate.
- Static assets must be local. API data remains server-backed. No offline CRUD, queued writes, background sync, or persistent authenticated catalog snapshots in the initial release.
- Design loading, empty, error, success, and permission-denied states. Meet keyboard and accessible-name requirements.

## 9. Testing, performance, and delivery

- Tests are mandatory: backend unit/API/integration/security/regression; frontend services/guards/forms/workflows; connector contract tests; RTL/LTR checks; migration tests.
- CI must run formatting, linting, type checks, backend/frontend tests, and production builds. Never weaken or delete tests merely to pass a build.
- Measure performance with reproducible representative workloads. Use pagination, bounded queries, batch extraction, bulk persistence, controlled pools, and avoid N+1/unbounded ORM loading.
- Evaluate PostgreSQL Full Text Search and `pg_trgm` for search needs. Do not claim unmeasured latency or capacity guarantees.
- Update specifications, ADRs, API contracts, tests, and operational documentation when affected.
- Never commit secrets, production data, unapproved metadata extracts, populated `.env` files, or unrelated changes.

## 10. Required workflow for every feature

1. Read this file, `docs/AGENTS-reference.md`, the Constitution, and relevant existing project artifacts.
2. Define user value, scope, acceptance criteria, permissions, security implications, and failure behavior before coding.
3. Use Spec Kit to produce and review the feature specification, clarify ambiguities, plan, tasks, and consistency analysis.
4. Obtain human approval of the spec and plan before implementation. Do not implement an ambiguous or unapproved design.
5. Implement in small dependency-ordered stages. Do not perform unrelated refactors.
6. Run applicable tests and quality gates; inspect the diff and verify no secrets or forbidden dependencies were introduced.
7. Compare the implementation against the spec, plan, tasks, Constitution, and detailed reference. Record remaining gaps rather than claiming completion.

## 11. Agent behavior

- Do not invent requirements, endpoints, database fields, credentials, source capabilities, or performance guarantees.
- When requirements are ambiguous or conflict, ask one focused question or document the conflict; do not guess.
- Before changing architecture, authentication, authorization, metadata identity, migrations, extraction semantics, deployment, or AI policy, identify the affected principle and obtain the required approval/ADR.
- Prefer the simplest maintainable solution that satisfies approved requirements. Explain important trade-offs and provide evidence from tests.
