# ==============================================================================
# Apex Operations API — Multi-Stage Production Dockerfile
# ==============================================================================
# Best Practices:
# 1. Multi-stage build 
# 2. non-root user (appuser, UID 10001).
# 3. healthcheck probe against /health/live.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies if needed for compiling
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into an isolated directory for clean copying
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Minimal Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner

# Install curl (used for healthchecks) and libpq5 runtime library
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Security: Create non-root system user and group (Least Privilege)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy installed Python packages from the builder stage
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application source code with proper non-root ownership
COPY --chown=appuser:appgroup app/ ./app/

# Switch execution context to the unprivileged non-root user
USER 10001:10001

# Expose HTTP application port
EXPOSE 8000

# Container healthcheck probe (Liveness check)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Start Uvicorn ASGI server
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
