# Data Catalog Project Constitution

**Status:** Active baseline  
**Version:** 1.0.0  
**Scope:** Enterprise Data Catalog — on-premises deployment  
**Authority:** This Constitution defines non-negotiable engineering principles for the project. `AGENTS.md` and `docs/AGENTS-reference.md` provide detailed implementation rules. Feature specifications, approved architecture decision records (ADRs), security policies, and API contracts refine these principles but must not silently contradict them.

## Core Principles

### Principle 1 — On-Premises Operation and Controlled Dependencies
The application MUST be deployable and operable within the organization's infrastructure.
- Runtime operation MUST NOT depend on public internet access, public CDNs, externally hosted fonts, or unapproved third-party services.
- Frontend scripts, styles, fonts, icons, and other required static assets MUST be locally bundled or served from approved internal infrastructure.
- Dependencies and deployment artifacts MUST be obtainable through approved internal mirrors, repositories, or controlled offline installation procedures.
- External network access, integrations, telemetry, and hosted services MUST require explicit review and approval.
- Development-time internet use is subject to organizational policy; production runtime independence is mandatory.

**Rationale:** The catalog connects to sensitive organizational data environments and must remain operational under internal-network and restricted-egress conditions.

**Verification:** Deploy and run the application in a representative environment with outbound public internet access disabled. Confirm that application startup, authentication, navigation, and core catalog workflows do not request public resources.

### Principle 2 — Approved Technology Stack and Clear Architecture Boundaries
The implementation MUST adhere strictly to the approved technology stack:
- Frontend: Angular 22, Standalone Components, TypeScript strict mode, PrimeNG, and Tailwind CSS 4.
- Backend: Python with FastAPI.
- API validation and contracts: Pydantic schemas.
- Persistence ORM: SQLAlchemy 2.x.
- Database migrations: Alembic.
- Central catalog repository: PostgreSQL.
- Background processing: Celery with Redis broker/cache.
- Reverse proxy and TLS termination: Nginx or an organization-approved equivalent.
- Initial authentication: local username/password authentication with Argon2id password hashing.

The repository MUST use a monorepo with distinct `/backend`, `/frontend`, `/infrastructure`, `/docs`, and `/scripts` areas.
- Backend business logic MUST be independent of HTTP routing and vendor-specific connector implementations.
- Frontend presentation MUST NOT make authoritative business-rule or authorization decisions.
- API routers MUST remain thin; use application/domain services for use cases and repositories for persistence queries.
- Connectors MUST be isolated behind a documented common contract.
- Technology versions MUST be mutually compatible, supported, and recorded in lockfiles and deployment documentation. Do not assume an unverified "latest" version or perform major upgrades without review.
- Java, Spring Boot, JPA, QueryDSL, Gradle, Lombok, and Liquibase MUST NOT be introduced into this project.

**Rationale:** Explicit boundaries reduce coupling, make connectors replaceable, and prevent unrelated legacy conventions or unapproved frameworks from entering the implementation.

**Verification:** Review repository structure, dependency manifests, module boundaries, and representative request-to-persistence flows. CI MUST build the backend and frontend independently.

### Principle 3 — Metadata-First Discovery, Not Business-Data Replication
The catalog's primary responsibility is discovery and governance of metadata, not replication of source business records.
- Source databases MUST be treated as read-only discovery targets by default.
- Connector credentials MUST possess only the minimum permissions required to inspect metadata.
- Ordinary discovery MUST NOT extract business rows.
- Any future sampling, profiling, or content inspection MUST be separately specified and approved, bounded by configurable limits, protected by masking/classification controls where applicable, and auditable.
- Metadata extraction MUST enforce timeouts, bounded retries, connection limits, and resource controls.
- Connectors MUST NOT execute arbitrary user-provided SQL or commands as part of normal metadata discovery.
- Vendor-specific capabilities and limitations MUST be documented.

The initial supported source types MUST be SQL Server, MySQL, Oracle, PostgreSQL, and MongoDB.

**Rationale:** Metadata discovery should minimize source-system impact and eliminate unnecessary risk of collecting or centralizing confidential business data.

**Verification:** Connector tests and code review MUST demonstrate read-only behavior, bounded execution, no default business-row extraction, safe timeout/retry behavior, and documented capabilities for each supported database type.

### Principle 4 — Preserve Source Semantics and Model Heterogeneous Metadata Correctly
The catalog MUST preserve the meaning and provenance of discovered metadata across heterogeneous source technologies.
- Relational metadata MUST represent supported database, schema, table/view, column, type, nullability, default, key, constraint, index, relationship, and source-description information.
- Original vendor type names and relevant vendor-specific attributes MUST be retained where normalization alone would lose meaning.
- MongoDB MUST be represented using document-oriented concepts, including database, collection, nested field paths, arrays, observed BSON types, optional fields, and mixed types.
- MongoDB samples MUST be explicitly identified as observations, not proof of a complete or guaranteed collection schema.
- Metadata identity and schema-change detection MUST be deterministic where possible, source-scoped, and documented where limitations exist.
- Added, changed, and removed metadata objects MUST be traceable through extraction history or equivalent versioned snapshots.
- Source-provided descriptions, user-authored descriptions, and any future AI-generated suggestions MUST remain distinct and retain provenance.
- Source changes MUST NOT silently overwrite user-authored descriptions.
- AI suggestions, if approved in a future phase, MUST remain proposals until an authorized human approves them.

**Rationale:** A useful catalog must represent heterogeneous source systems faithfully and preserve the origin and evolutionary history of its metadata.

**Verification:** Use connector fixtures and integration tests covering relational structures, MongoDB nested/mixed structures, metadata changes, description provenance, and extraction-history behavior.

### Principle 5 — Security, Least Privilege, and Server-Enforced Authorization
Security MUST be built into every layer and MUST fail closed.
- Initial authentication MUST use local accounts. AD/LDAP/SSO is out of initial scope unless separately approved.
- Passwords MUST be stored only as secure Argon2id hashes; plaintext passwords and reversible password storage are strictly prohibited.
- Source connection credentials MUST be encrypted at rest using an approved key-management design. Encryption keys MUST NOT be stored alongside ciphertext in the application database or source repository.
- Secrets MUST never appear in API responses, frontend state, logs, exception messages, screenshots, or committed files.
- The authorization model MUST support users with multiple roles, explicit permissions, and category/source scopes.
- Category-level permission inheritance MUST be explicit. The initial behavior MUST be inheritance from a parent category to its descendants, subject to approved authorization rules.
- Effective permissions MUST be calculated and enforced by the backend for every protected operation.
- The system MUST deny access by default. Missing, ambiguous, or failed authorization checks MUST NOT grant access.
- UI hiding or disabled controls MUST never be treated as a security boundary.
- Administrative changes to users, roles, role assignments, permissions, category access, source access, and credentials MUST be auditable.
- Connector registration MUST be protected against SSRF and unauthorized access to internal infrastructure endpoints.
- Authentication endpoints MUST enforce rate limiting and protections against account enumeration.
- Transport security, secure headers, input validation, parameterized queries, and dependency vulnerability review are mandatory.

**Rationale:** The catalog centralizes sensitive structural information and connection configuration; a UI-only or permissive authorization model is unacceptable.

**Verification:** Security tests MUST cover allowed and denied access, multiple-role permission aggregation, inherited category access, direct source access, credential redaction, authentication protections, and SSRF/network restrictions.

### Principle 6 — Explicit API Contracts and Safe Data Access
All API boundaries MUST be explicit, validated, and version-conscious.
- Pydantic request and response schemas MUST be used for all endpoints. SQLAlchemy entities MUST NOT be exposed directly as API contracts.
- Request, response, and persistence models MUST remain separated where their responsibilities differ.
- Every endpoint MUST return only fields the caller is authorized to see.
- Password hashes, encrypted secrets, tokens, internal configuration, and raw vendor errors MUST never be serialized to clients.
- API behavior MUST use consistent conventions for pagination, filtering, sorting, validation, and errors.
- API breaking changes MUST be documented and coordinated with frontend contracts and tests.
- Database queries MUST be parameterized and scoped to the authenticated user's effective permissions.
- Search and browsing MUST query the central metadata repository rather than fan out to all source databases for each user request.
- Large result sets MUST be paginated or otherwise bounded.

**Rationale:** Stable contracts and explicit field selection prevent accidental data exposure and eliminate tight coupling between frontend, backend, and persistence layers.

**Verification:** API tests MUST validate schemas, pagination, error contracts, sensitive-field exclusion, and permission-filtered results.

### Principle 7 — Reliable, Controlled, and Auditable Background Extraction
Long-running and scheduled extraction MUST execute asynchronously.
- Celery workers with Redis MUST be used for background extraction and long-running work.
- Job state MUST be persisted and observable, including job type, source/scope, requester, lifecycle state, timestamps, retry count, and sanitized failure details.
- Extraction tasks MUST be safe to retry without corrupting inventory or duplicating metadata, and SHOULD be idempotent.
- Duplicate or overlapping jobs for the same source/scope MUST be prevented unless explicitly supported.
- Retry policies MUST be bounded, use backoff for transient failures, and distinguish transient errors from permanent authentication/configuration failures.
- Worker concurrency, per-source connection limits, batch sizes, and global resource use MUST be bounded and configurable.
- Scheduling and execution history MUST be centrally recorded.
- Partial failure MUST be recoverable without falsely marking incomplete metadata as successfully refreshed.
- Extraction requests, schedule changes, outcomes, and privileged actions MUST be auditable.

**Rationale:** Uncontrolled discovery can overload source systems, generate inconsistent inventory, or make failures impossible to diagnose.

**Verification:** Tests MUST cover job state transitions, retry behavior, idempotency, duplicate-run prevention, partial failure, scheduling, and concurrency limits.

### Principle 8 — PostgreSQL Integrity, Controlled Migrations, and Traceable Change
PostgreSQL is the central repository for catalog application data, including identity, authorization, source registrations, metadata, descriptions, extraction history, schedules, and audit events.
- The project MUST start with one application schema. Additional schemas are permitted only when a documented need justifies them and an approved ADR defines the privilege model, migration plan, rollback/recovery strategy, and tests.
- One schema per source database, user, or Python package MUST NOT be created by default.
- SQLAlchemy 2.x typed mappings and explicit transaction boundaries MUST be used.
- Every persistent schema change MUST be represented by a reviewed Alembic migration.
- Autogenerated migrations are drafts and MUST be reviewed before execution.
- Destructive changes MUST include data-impact analysis, backup/restore considerations, and explicit approval.
- UUIDs SHOULD be used for application entity identifiers by default; exceptions require a documented technical reason.
- Timestamps MUST be timezone-aware and stored consistently in UTC.
- Constraints and indexes MUST be used to enforce integrity and support measured access patterns.
- JSONB MUST be used only for genuinely flexible metadata, not as a substitute for well-defined relational attributes.
- Generic creation/update timestamps MUST NOT replace the dedicated audit-event history.

**Rationale:** The central repository is the system of record for catalog state; its integrity and migration history must be strictly controlled.

**Verification:** CI and release checks MUST validate Alembic migration consistency and run migration tests against supported PostgreSQL environments. Schema-strategy exceptions require an ADR.

### Principle 9 — Immutable, Useful Audit History and Operational Observability
Security- and governance-relevant actions MUST be traceable.
Audit events MUST capture, as applicable:
- Successful and failed login/logout events.
- User, role, permission, and role-assignment changes.
- Category and source registration or modification.
- Connection configuration changes and credential rotation events (never credential values).
- Extraction requests, schedule changes, execution outcomes, and privileged administrative actions.
- Metadata description, ownership, classification, and approval changes.

Each event MUST include actor, action, entity type and identifier, timestamp, outcome, request/correlation ID, and permitted source context such as client IP where policy permits.
- Before/after values MUST be selective and MUST redact secrets and sensitive payloads.
- Ordinary users MUST NOT be able to alter or delete audit history.
- Application logs MUST be structured and correlated, but MUST NOT become a duplicate store of credentials or business data.
- Operational monitoring MUST track API health/latency/errors, PostgreSQL and Redis health, worker queue depth, extraction duration/failures, and source connectivity.
- Liveness and readiness endpoints MUST be distinct.
- Backup and restore procedures MUST cover the central repository and the encryption-key recovery process. Restore procedures MUST be tested periodically.

**Rationale:** Governance requires accountability, while operations require sufficient safe telemetry to diagnose failures and capacity bottlenecks.

**Verification:** Audit tests MUST verify event creation, actor attribution, redaction, and access restrictions. Operational documentation MUST describe health checks, backup, restore, and key recovery procedures.

### Principle 10 — Usable, Accessible, Localized Angular Experience
The frontend MUST provide a maintainable and accessible enterprise interface.
- Angular MUST run as a client-rendered SPA. SSR, SSG, prerendering, hydration, and server rendering are explicitly out of scope unless approved by a new ADR.
- PrimeNG and Tailwind CSS 4 are the approved UI foundations. `ngbase` and the legacy `../base/angularbase` library MUST NOT be used.
- The frontend MUST use Standalone Components, strict TypeScript and template checking, typed forms, lazy-loaded feature routes, and Signals where appropriate.
- Feature and reusable components MUST separate TypeScript, HTML, and SCSS files by default.
- Components MUST remain focused on presentation and interaction; API access and reusable business behavior belong in services/facades.
- Persian RTL and English LTR layouts MUST be supported. Direction and locale MUST be centrally managed.
- Styling MUST prefer CSS logical properties and direction-aware utilities over physical left/right assumptions.
- Interactive controls MUST have accessible names, form controls MUST have programmatic labels, and keyboard interaction MUST be supported.
- Loading, empty, error, success, and permission-denied states MUST be designed explicitly.
- User-visible strings MUST use the project's localization resources.
- Static assets MUST be locally bundled. The offline scope is strictly assets only: API data remains server-backed.
- Offline CRUD, queued writes, background synchronization, service-worker API caching, or persistent authenticated catalog snapshots MUST NOT be implemented in the initial release.

**Rationale:** The catalog is an internal business application; usability, accessibility, localization, and predictable online behavior take priority over public search indexing or offline data editing.

**Verification:** Review shared screens in both RTL and LTR, test keyboard and accessible-name behavior, verify responsive layouts, and confirm the deployed SPA loads static assets without public network calls.

### Principle 11 — Mandatory Testing and Quality Gates
Tests are a release requirement, not optional documentation.
- Backend tests MUST include unit, API/integration, security, and regression coverage appropriate to the changed behavior.
- Frontend tests MUST cover services, guards, non-trivial components, forms, permission-aware behavior, and critical user workflows.
- Connector contract tests MUST cover each supported source type. Tests requiring external infrastructure MUST be clearly identified and run in an appropriate controlled environment.
- Authorization, credential protection, metadata normalization, schema-change detection, job lifecycle, retry behavior, and audit behavior MUST have targeted automated tests.
- RTL/LTR behavior MUST be tested for shared and high-use UI components.
- CI MUST run formatting, linting, type checks, backend tests, frontend tests, and production builds.
- Security-sensitive changes MUST include targeted security tests and review.
- Tests MUST NOT be skipped, deleted, or weakened solely to make a build pass. Invalid tests must be corrected or replaced with documented reasoning.
- Performance tests MUST use representative volumes and document the test environment, method, and results. Do not claim unmeasured guarantees.

**Rationale:** The catalog's permission model, metadata correctness, and extraction reliability are too critical to rely on manual verification alone.

**Verification:** A change is not complete until all applicable automated checks pass and required test evidence is available in CI or the review record.

### Principle 12 — Scale, Performance, and Resilience Must Be Measured
The architecture MUST be designed for the initial planning scale and verified as the catalog expands.
- Support approximately 140,000 relational tables across ~700 database instances and approximately 600 users as planning assumptions, without hard-coding these figures as limits.
- The system MUST use bounded pagination, batch extraction, bulk persistence, and controlled connection pools.
- Queries MUST avoid N+1 patterns and unbounded ORM loading.
- PostgreSQL indexes, query plans, Redis, worker concurrency, and source connection limits MUST be tuned using measured workloads.
- Search MUST query the central catalog repository. PostgreSQL Full Text Search and `pg_trgm` MUST be evaluated for full-text and fuzzy search needs.
- Extraction MUST tolerate partial failure and support safe retry.
- Performance targets MUST be defined from product requirements and validated with reproducible tests; arbitrary universal latency or Lighthouse score guarantees MUST NOT be imposed without measurement.
- Capacity and load-test results MUST state hardware, dataset size, concurrency, and methodology.

**Rationale:** The catalog manages a substantial metadata inventory across multiple source systems; performance must be demonstrated under realistic conditions rather than assumed.

**Verification:** Maintain repeatable load/performance tests for representative catalog inventory, concurrent users, search, and extraction workloads. Review query plans and resource utilization for material changes.

### Principle 13 — AI Is Disabled Until Explicitly Approved
AI-assisted metadata descriptions, classification, and enrichment are future capabilities only.
- No AI provider, model endpoint, API key, external AI connector, or metadata transmission to an AI service may be enabled in the initial release without explicit product, security, and organizational approval.
- The architecture MAY define isolated extension points for a future AI service, but MUST NOT introduce an operational dependency on AI.
- Any future AI feature MUST document data categories sent, provider/hosting location, retention, access controls, security review, cost, failure behavior, and human oversight.
- AI-generated descriptions or classifications MUST be marked as suggestions with provenance and MUST NOT silently replace source or user-authored metadata.
- An authorized human MUST approve AI suggestions before they become authoritative catalog content.

**Rationale:** Metadata can reveal sensitive organizational structure. Future AI value does not justify unapproved disclosure or unreviewed automated alterations.

**Verification:** Dependency, configuration, network-egress, and code reviews MUST confirm that no AI service is active in the initial release. Future activation requires an approved ADR and security sign-off.

### Principle 14 — Documentation, Decisions, and Maintainable Delivery
Implementation decisions MUST be explainable and reproducible.
- Significant architecture decisions MUST be recorded as ADRs with context, decision, alternatives, consequences, and security/operational impact.
- Connector capabilities, API contracts, data models, authorization semantics, extraction behavior, deployment, backup/restore, and troubleshooting MUST be documented.
- Feature specifications MUST define user value, scope, acceptance criteria, security implications, and failure behavior.
- Changes affecting API contracts, metadata identity, authorization, migrations, extraction, or deployment MUST update relevant documentation and tests.
- Avoid speculative abstractions and premature generalization. Prefer the simplest design that satisfies approved requirements and preserves required extension points.
- Code MUST be reviewable, typed where supported, consistently formatted, and free of unrelated changes.
- The Definition of Done below applies to all feature and bug-fix work.

**Rationale:** The system evolves across multiple connectors and teams; explicit decisions and operational knowledge reduce hidden dependencies and regressions.

**Verification:** Pull requests MUST identify affected requirements, tests, migrations, documentation, and ADRs. Reviewers MUST be able to reproduce the relevant build and test steps.

## Operational Constraints and Precedence

The project delivers an on-premises Enterprise Data Catalog for discovering, describing, organizing, searching, governing, and auditing metadata across heterogeneous organizational data sources. The system must be secure by default, maintainable, testable, operationally reliable, and capable of growing beyond its initial planning scale.

Initial planning assumptions are approximately 700 registered database instances, an average of 200 relational tables per instance (approximately 140,000 tables), and approximately 600 users. These are capacity-planning estimates, not hard-coded product limits or performance guarantees.

When requirements conflict, apply this strict order of precedence:

1. Applicable law, organizational security policy, and data-protection requirements.
2. This Constitution and approved Architecture Decision Records (ADRs).
3. Approved feature specifications and API contracts.
4. `AGENTS.md`, `docs/AGENTS-reference.md`, and local implementation conventions.
5. Individual implementation preference.

A conflict MUST be raised and resolved explicitly. Agents and contributors MUST NOT silently invent requirements or bypass a higher-priority constraint.

## Definition of Done

A feature, change, or bug fix is complete only when all applicable criteria are met:

1. Approved specification and acceptance criteria are satisfied.
2. Architecture and security constraints in this Constitution and `AGENTS.md` are followed.
3. Backend business rules are implemented in the appropriate service/domain layer.
4. API inputs and outputs use explicit Pydantic schemas and exclude unauthorized/sensitive fields.
5. Every protected operation enforces authorization on the backend and has positive and negative tests.
6. Persistent schema changes have reviewed Alembic migrations.
7. Connector behavior is read-only by default, bounded, timeout-protected, and safe in logs.
8. Background jobs have valid state transitions, bounded retries, and duplicate-run protection where applicable.
9. Required audit events are emitted with appropriate redaction and access restrictions.
10. Applicable unit, integration, security, regression, and performance tests pass.
11. Frontend handles loading, empty, error, and permission-denied states.
12. Shared/localized UI works in RTL and LTR where applicable and meets accessibility expectations.
13. Runtime static assets are local; no unapproved public internet dependency is introduced.
14. No SSR/SSG, PWA API caching, offline writes, or AI integration is introduced without an approved decision.
15. Formatting, linting, type checks, backend/frontend tests, and production builds pass.
16. Documentation, deployment guidance, and ADRs are updated where needed.
17. No secrets, production data, unapproved metadata extracts, or local environment files are committed.

## Governance

This Constitution is the project's baseline engineering contract and supersedes all undocumented informal practices.

### Amendment Procedure
- Any proposed exception or modification MUST state the affected principle, reason, scope, risks, alternatives considered, migration/rollback implications, and verification plan.
- Security, privacy, credential-handling, and authorization exceptions require explicit sign-off from organizational authorities; a code review alone is insufficient.
- Architectural exceptions MUST be recorded in an approved ADR prior to implementation, except for a documented emergency fix that is reviewed and recorded immediately afterward.
- Amendments MUST identify impacted specifications, code, tests, and operational documentation.
- When this Constitution changes, `AGENTS.md`, `docs/AGENTS-reference.md`, relevant Spec Kit artifacts, and active feature plans MUST be reconciled. Conflicts MUST be resolved explicitly rather than leaving contradictory instructions in the repository.

### Versioning Policy
This Constitution follows Semantic Versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Backward-incompatible governance changes, removal of principles, or substantial redefinitions of non-negotiable constraints.
- **MINOR**: New principles or sections added, or materially expanded governance guidance without weakening existing rules.
- **PATCH**: Clarifications, wording improvements, typo fixes, or non-semantic structural refinements.

### Compliance Review Expectations
- All feature specifications, implementation plans, pull requests, and automated quality gates MUST verify compliance with this Constitution and `AGENTS.md`.
- Violations or unapproved deviations are blocking release blockers.
- Complexity MUST be justified against simplicity and approved scope.
- Runtime development guidance and detailed rules are anchored in `docs/AGENTS-reference.md` and `AGENTS.md`.

### Change History

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-11-02 | Initial constitution for the on-premises Enterprise Data Catalog, based on approved project baseline and decisions: Angular SPA (no SSR), local assets only, PostgreSQL schema strategy by recommendation, no ngbase, strict testing, local authentication, and AI disabled pending approval. |

**Version**: 1.0.0 | **Ratified**: 2026-11-02
