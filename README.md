# MetaSphere — Enterprise Data Catalog

MetaSphere is an on-premises, air-gapped Enterprise Data Catalog designed for discovering, describing, organizing, searching, governing, and auditing metadata across heterogeneous databases and enterprise storage systems.

---

## 1. Monorepo Architecture & Technology Stack

MetaSphere is structured as a strict monorepo adhering to the [Project Constitution](.specify/memory/constitution.md):

- **`/backend`**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x (synchronous), Alembic migrations, Celery asynchronous workers, and Redis client.
- **`/frontend`**: Angular 22 Single Page Application (SPA), Standalone Components, PrimeNG, Tailwind CSS 4, PrimeIcons, and Vitest test runner with full RTL/LTR bidirectional support.
- **`/infrastructure`**: Central PostgreSQL 16+ repository and Redis 7+ configurations (Docker Compose development and production orchestration).
- **`/scripts`**: Root verification (`verify.ps1`), air-gap packaging (`package-airgap.ps1`), and CI/CD tools.
- **`/docs`**: Architectural decision records, setup guides, and project governance specifications.

---

## 2. Core Governance Constraints (Constitution Baseline)

1. **100% On-Premises & Offline Independence**: Production runtime operates with zero internet access, no external CDNs, no remote fonts, and zero unapproved telemetry.
2. **Metadata-First**: Discovers, governs, and catalogs metadata without replicating business data rows.
3. **Security by Default**: Argon2id password hashing, encrypted credentials at rest, fail-closed configuration, and automated secret-masking filters in logging.
4. **Clean Scope Boundaries**: The initial foundation feature strictly isolates runtime, persistence, and observability foundations from deferred features (connectors, catalog search, authentication, and AI services).

---

## 3. Getting Started

Detailed developer onboarding instructions are available in [docs/dev-setup.md](docs/dev-setup.md).

Quick commands:
```powershell
# Run all automated quality gates (Ruff, Mypy, Pytest, ESLint, Vitest, Build)
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

---

## 4. Current Feature Status

- **Feature**: `001-project-foundation` ([Specification](specs/001-project-foundation/spec.md) | [Plan](specs/001-project-foundation/plan.md) | [Tasks](specs/001-project-foundation/tasks.md))
- **Status**: Completed and verified via automated test gates.
