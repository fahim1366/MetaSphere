# ==============================================================================
# MetaSphere Backend Production Dockerfile (Air-Gapped Multi-Stage)
# ==============================================================================

# Stage 1: Build wheelhouse from locked dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock pyproject.toml ./

RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/build/wheels -r requirements.lock

# Stage 2: Minimal, secure, non-root runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime PostgreSQL client library
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN useradd -u 10001 -m -s /bin/bash appuser

# Install pre-built wheels offline
COPY --from=builder /build/wheels /app/wheels
COPY requirements.lock ./
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels -r requirements.lock && \
    rm -rf /app/wheels

# Copy application source and migration configuration
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser app ./app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
