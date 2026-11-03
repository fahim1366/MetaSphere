# Quickstart & Verification Guide: Project Foundation

**Feature**: `001-project-foundation`  
**Date**: 2026-11-02  
**Status**: Completed  

This guide provides step-by-step instructions for bootstrapping the MetaSphere development environment in **Hybrid Mode**, running automated quality gates, and verifying health probes, background processing, and air-gapped readiness.

---

## 1. Prerequisites (Windows Workstation)

Ensure the following pinned tools are installed on your Windows host:
- **Docker Desktop** (v24+ with Compose v2+)
- **Python 3.12** (pinned runtime; verify with `python --version`)
- **Node.js 22.22.3 Active LTS** with **npm 10.9.8** (pinned frontend runtime; verify with `node -v` and `npm -v`)
- **PowerShell 7+** or Windows PowerShell 5.1

---

## 2. Dependency Supply Modes: Connected vs. Air-Gapped

### Mode A: Connected Staging / Online Developer Workstation
When outbound network access to approved package repositories exists:
- Backend: `pip install -e ".[dev]"`
- Frontend: `npm ci`

### Mode B: Air-Gapped / Completely Offline Workstation
When operating on an isolated workstation without outbound network access:
- **Python Wheels**: Installed from a pre-mirrored local wheelhouse directory:
  ```powershell
  pip install --no-index --find-links=./wheelhouse/ -e ".[dev]"
  ```
- **Node Modules**: Installed from a pre-populated local npm cache tarball:
  ```powershell
  npm ci --prefer-offline --cache ./npm-cache
  ```
- **Container Images**: Imported from an approved image archive bundle:
  ```powershell
  docker load -i metasphere-images-v0.1.0.tar.gz
  ```

---

## 3. Step-by-Step Setup Sequence (Hybrid Mode)

### Step 3.1: Start Local Datastores (PostgreSQL & Redis)
From the repository root in PowerShell:
```powershell
# Start PostgreSQL 16 and Redis 7 in detached mode
docker compose -f infrastructure/docker-compose.yml up -d

# Verify both containers report healthy status
docker compose -f infrastructure/docker-compose.yml ps
```
**Expected Outcome**: Both `metasphere-postgres` and `metasphere-redis` report `Up (healthy)`.

---

### Step 3.2: Backend Setup & Database Migration
```powershell
cd backend

# Create and activate Python 3.12 virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (use Mode A or Mode B as appropriate)
pip install -e ".[dev]"

# Initialize environment configuration from sanitized template
Copy-Item .env.example .env

# Apply initial baseline database migration (synchronous Alembic runner)
alembic upgrade head
```
**Expected Outcome**: Alembic executes revision `0001_initial_baseline` and stamps the PostgreSQL database without error.

---

### Step 3.3: Start Background Worker & Backend API
In terminal 1 (Celery Worker):
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
# On Windows, Celery uses -P solo to avoid POSIX process-forking limitations
celery -A app.jobs.celery_app worker --loglevel=info -P solo
```

In terminal 2 (FastAPI Server):
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```
**Expected Outcome**: FastAPI logs display application startup with correlation ID logging; Uvicorn is serving on `http://localhost:8000`.

---

### Step 3.4: Frontend Setup & Application Shell
In terminal 3 (Angular Frontend):
```powershell
cd frontend

# Install pinned dependencies
npm ci

# Start the Angular development server
npm start
```
**Expected Outcome**: Angular development server compiles and serves on `http://localhost:4200`.

---

## 4. End-to-End Verification Scenarios

### Scenario A: Verify Liveness and Dependency Readiness Probes
Run in PowerShell:
```powershell
# 1. Test process liveness (< 5ms response latency)
Invoke-RestMethod -Uri http://localhost:8000/health/live
# Expected: { "status": "live", "service": "metasphere-backend", "version": "0.1.0" }

# 2. Test overall readiness (PostgreSQL & Redis connected, P95 < 25ms local design target)
Invoke-RestMethod -Uri http://localhost:8000/health/ready
# Expected: HTTP 200 with { "status": "ready", "components": { "postgres": { "status": "connected" }, "redis": { "status": "connected" } } }
```

### Scenario B: Verify Failure Recovery (Circuit-Breaker & Fail-Closed Check)
```powershell
# Stop PostgreSQL temporarily to simulate infrastructure failure
docker compose -f infrastructure/docker-compose.yml stop postgres

# Query readiness probe
try {
    Invoke-RestMethod -Uri http://localhost:8000/health/ready
} catch {
    $_.Exception.Response.StatusCode # Expected: 503 Service Unavailable
}

# Restart PostgreSQL
docker compose -f infrastructure/docker-compose.yml start postgres
Start-Sleep -Seconds 3

# Query readiness probe again once recovered
Invoke-RestMethod -Uri http://localhost:8000/health/ready # Expected: HTTP 200 OK
```

### Scenario C: Verify Frontend Bidirectional Layout & Theme
1. Open browser at `http://localhost:4200`.
2. Confirm the initial shell renders with PrimeNG styling and Tailwind CSS 4 theme tokens.
3. Toggle the language switch to `فارسی (RTL)`.
4. Inspect the root HTML element: confirm `dir="rtl"` and `lang="fa"` are set, and layout utilities dynamically adjust to the start/end alignment using CSS logical properties.
5. Confirm the live backend status widget displays `Connected` for both PostgreSQL and Redis.

---

## 5. Automated Quality Gate Verification

From the repository root, run the offline verification sequence:

```powershell
# Backend linting, formatting check, and static type analysis
cd backend
ruff check .
ruff format --check .
mypy app

# Backend automated test suite and latency benchmark
pytest tests -v
pytest tests/api/test_health_bench.py -v

# Frontend linting and Vitest unit testing (headless, browserless)
cd ../frontend
npm run lint
npm run test
```
**Expected Outcome**: All static analysis, type checks, benchmarks, and unit tests pass with 0 errors and 0 warnings without requiring outbound internet access.
