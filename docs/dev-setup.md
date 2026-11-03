# Developer Setup Guide: Hybrid Local Development

## 1. Prerequisites & Pinned Toolchain

To develop and test MetaSphere locally in **Hybrid Mode**, ensure your workstation has:

- **OS**: Windows 10/11 (or Linux / macOS with equivalent paths)
- **Python**: `3.12` (pinned via `.python-version` and `pyproject.toml`)
- **uv**: `0.5+` (recommended package manager) or standard `pip`
- **Node.js**: `22.22.3` Active LTS (pinned in `.nvmrc` and `frontend/package.json`)
- **npm**: `10.9.8+`
- **Docker & Docker Compose**: Docker Desktop 24+ with Compose v2+ (for PostgreSQL 16 & Redis 7 containers)

---

## 2. Quickstart Step-by-Step

### Step 1: Clone and Enter Repository
```bash
git clone https://github.com/fahim1366/MetaSphere.git
cd MetaSphere
```

### Step 2: Start Local Infrastructure (PostgreSQL & Redis)
In the repository root:
```bash
docker compose -f infrastructure/docker-compose.yml up -d
```
Verify containers are healthy:
- `metasphere-postgres`: port 5432
- `metasphere-redis`: port 6379

### Step 3: Backend Setup (Python 3.12)
Navigate to `/backend`:
```bash
cd backend
cp .env.example .env

# Create and activate Python 3.12 virtual environment
uv venv --python 3.12 .venv
source .venv/Scripts/activate   # or .venv\Scripts\Activate.ps1 in PowerShell

# Connected installation:
uv pip install -r requirements.lock

# Offline installation (from pre-built wheelhouse):
# pip install --no-index --find-links=../wheelhouse -r requirements.lock
```

### Step 4: Run Baseline Database Migrations
Inside `/backend` with virtual environment active:
```bash
alembic upgrade head
```

### Step 5: Start Backend Development Server
Inside `/backend`:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Verify backend endpoints:
- Liveness probe: `http://localhost:8000/health/live`
- Readiness probe: `http://localhost:8000/health/ready`

### Step 6: Frontend Setup (Angular 22)
Open a new terminal and navigate to `/frontend`:
```bash
cd frontend

# Connected installation:
npm install

# Offline installation:
# npm ci --offline --cache ../.npm-cache

# Start Angular development server:
npm start
```
Open `http://localhost:4200` in your browser. The application shell and live readiness dashboard will display.

---

## 3. Automated Quality Verification

To run all deterministic quality checks (Ruff, Mypy, Pytest, ESLint, Vitest, and Angular Build):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

To run with live integration tests (requires Docker containers up):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -RunIntegration
```

To run latency benchmarks:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1 -RunBenchmark
```

---

## 4. Background Task Worker (Celery)

To start the Celery background worker locally on Windows:
```bash
cd backend
celery -A app.jobs.celery_app.celery_app worker --pool=solo -l info
```
