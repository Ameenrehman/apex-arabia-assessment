# Apex Operations API — Junior DevOps Engineer Assessment

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-green.svg)](Dockerfile)
[![Tests](https://img.shields.io/badge/Tests-8%2F8%20Passed-brightgreen.svg)](tests/)
[![Security](https://img.shields.io/badge/Security-Non--Root%20UID%2010001-orange.svg)](Dockerfile)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](requirements.txt)

A production-ready, containerized **Apex Operations API** designed for reproducible local deployment, automated CI/CD gating, structured observability, and zero-downtime rollback safety.

---

## 1. Quickstart (Run in 2 Commands)

```bash
# 1. Setup environment configuration
cp .env.example .env    # Linux/macOS
# copy .env.example .env # Windows

# 2. Pull verified images from Docker Hub and start containers
docker compose pull
docker compose up -d
```

Once running:
- **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Liveness Probe:** `http://localhost:8000/health/live`
- **Readiness Probe:** `http://localhost:8000/health/ready`
- **Prometheus Metrics:** `http://localhost:8000/metrics`

---

## 2. Architecture & Design Principles

```
                       +-----------------------------+
                       |    Client / Load Balancer   |
                       +--------------+--------------+
                                      |
                                      v HTTP :8000
                       +-----------------------------+
                       | Container: apex-api         |
                       | - Non-root (UID 10001)      |
                       | - FastAPI + Uvicorn         |
                       | - Structured JSON Logging   |
                       | - Readiness & Liveness      |
                       +--------------+--------------+
                                      |
                                      | TCP :5432 (Internal Network)
                                      v
                       +-----------------------------+
                       | Container: apex-db          |
                       | - PostgreSQL 16 Alpine      |
                       | - Healthcheck: pg_isready   |
                       | - Persistent Named Volume   |
                       +--------------+--------------+
                                      |
                                      v
                       +-----------------------------+
                       | Volume: apex_postgres_data  |
                       +-----------------------------+
```

### Key Engineering Decisions:
1. **Multi-Stage Dockerfile:** Separates compilation/build dependencies from runtime. Minimizes final image size and attack surface.
2. **Non-Root Execution:** Container runs strictly as unprivileged user `appuser` (UID 10001, GID 10001) for container escape mitigation.
3. **Dual Health Probes:**
   - **`/health/live` (Liveness):** Process is alive $\rightarrow$ prevents unnecessary container restarts.
   - **`/health/ready` (Readiness):** Active DB connectivity check $\rightarrow$ load balancers do not route traffic until ready.
4. **Structured JSON Logs with Correlation IDs:** Every request is tagged with an `X-Request-ID` UUID, tracking execution latency and status codes.
5. **No Overhead:** No unnecessary complexity (e.g., massive Kubernetes manifests or Makefile wrappers). Everything runs via standard Docker Compose and Python tooling.

---

## 3. Endpoints & Verification Commands

Verify each endpoint using `curl`:

```bash
# 1. Liveness check (HTTP 200)
curl -i http://localhost:8000/health/live

# 2. Readiness check (HTTP 200 with DB connected)
curl -i http://localhost:8000/health/ready

# 3. Create an operational task (HTTP 201 Created)
curl -X POST http://localhost:8000/api/v1/operations \
  -H "Content-Type: application/json" \
  -d '{"title": "Deploy Service Mesh", "service_name": "core-mesh", "environment": "production", "status": "completed"}'

# 4. List operational tasks (HTTP 200)
curl -i http://localhost:8000/api/v1/operations

# 5. Prometheus metrics (HTTP 200)
curl -i http://localhost:8000/metrics
```

---

## 4. Automated Tests Suite (6 Required Checks)

The repository includes a comprehensive test suite with 8 tests covering the 6 required assessment areas:

```bash
# Run tests locally
pytest -v
```

| Check # | Test File | Description |
| :---: | :--- | :--- |
| **Check 1** | `tests/test_health_live.py` | Liveness probe returns HTTP 200 & status "alive" |
| **Check 2** | `tests/test_health_ready.py` | Readiness probe returns HTTP 200 when database connected |
| **Check 3** | `tests/test_operations_api.py` | Operations CRUD workflow (Create, Read, List, 404 validation) |
| **Check 4** | `tests/test_input_validation.py` | Schema validation rejects malformed payloads (HTTP 422) |
| **Check 5** | `tests/test_db_failure_mode.py` | Readiness probe gracefully returns HTTP 503 on database disconnect |
| **Check 6** | `tests/test_intentional_failure.py` | **Intentional failure test** demonstrating CI gate deployment blocking |

### Demonstrating the Intentional Failure (CI Gate Proof)
To trigger the intentional failure and prove that broken tests halt the CI pipeline:

```bash
# Python:
python -c "import os, pytest; os.environ['SIMULATE_INTENTIONAL_FAILURE'] = 'true'; pytest.main(['tests/test_intentional_failure.py', '-v'])"
```

---

## 5. Safe Rollback Procedure

When a bad release is detected, rollback can be executed either via semantic version tags (`v1.0.0`) or immutable Git commit SHAs (`sha-xxxxxxx`):

```bash
# 1. Switch back to previous known-good tag or commit SHA
export APP_IMAGE_TAG=sha-626120f     # Linux/macOS
# $env:APP_IMAGE_TAG = "sha-626120f" # Windows PowerShell

# 2. Pull target image & re-apply Docker Compose (zero downtime recreate)
docker compose pull apex-api
docker compose up -d apex-api

# 3. Confirm service health
curl -f http://localhost:8000/health/ready
```

*(Or run the automated helper: `./scripts/rollback.sh sha-626120f` / `.\scripts\rollback.ps1 -TargetTag sha-626120f`)*

---

## 6. CI/CD Pipeline & Docker Hub Automated Release

The GitHub Actions workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) automates quality gating and delivery:

1. **Linting (Ruff):** Validates code style and imports.
2. **Automated Tests (Pytest):** Runs 8 tests covering healthchecks, database isolation, CRUD, and failure modes.
3. **Security Vulnerability Scan (Trivy):** Scans the repository and dependencies for High/Critical CVEs.
4. **Gated Container Build & Push:** Only triggers if all tests and security scans succeed! Pushes tagged images to Docker Hub: [`ameen2607/apex-arabia`](https://hub.docker.com/r/ameen2607/apex-arabia) with Git commit SHA and `latest` tags.
5. **Path Filtering:** Pipeline only triggers on changes to application code, tests, Dockerfile, or workflow configs (documentation changes never trigger unnecessary builds).
6. **Manual Execution & Failure Testing:** Supports manual triggers (`workflow_dispatch`) with an interactive toggle to simulate a test failure and prove deployment gating.

---

## 7. Failure Investigation & Log Triage Demo

We have included a full incident demonstration script and investigation report:
- **Demonstration Script:** Run `powershell .\scripts\simulate_db_failure.ps1` (or `./scripts/simulate_db_failure.sh`).


---

## 8. Project Documentation Index

- **[Operations Runbook (RUNBOOK.md)](RUNBOOK.md):** Complete deploy, rollback, incident response, and troubleshooting procedures.
- **[Architecture & Decision Memo (docs/DECISION_MEMO.md)](docs/DECISION_MEMO.md):** Trade-offs, tooling justifications, and $27/mo cloud migration roadmap.
- **[System Architecture Diagrams (docs/architecture.md)](docs/architecture.md):** Mermaid topology, CI gating, and request lifecycle diagrams.
- **[AI Disclosure (docs/AI_DISCLOSURE.md)](docs/AI_DISCLOSURE.md):** Transparent disclosure conforming to Section 3 of the assessment guidelines.
