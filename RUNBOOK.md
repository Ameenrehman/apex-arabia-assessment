# Apex Operations API — Production Operations Runbook

---

## 1. Overview & Service Architecture

The **Apex Operations API** provides automated operational task tracking and service status observability. It runs as a containerized service backed by a PostgreSQL database.

```
                      +-----------------------------+
                      | Client / Load Balancer     |
                      +--------------+--------------+
                                     |
                                     v HTTP:8000
                      +-----------------------------+
                      | Container: apex-api         |
                      | - Non-root (UID: 10001)     |
                      | - FastAPI / Uvicorn         |
                      | - Structured JSON Logging   |
                      +--------------+--------------+
                                     |
                                     | TCP:5432 (Internal Network)
                                     v
                      +-----------------------------+
                      | Container: apex-db          |
                      | - PostgreSQL 16 Alpine      |
                      | - Persistent Named Volume   |
                      +-----------------------------+
```

---

## 2. Deployment Procedures

### 2.1 Pre-Flight Verification Checklist
Before deploying, ensure:
1. Docker Engine ($\ge 24.0$) and Docker Compose ($\ge v2$) are running.
2. Port `8000` (API) and `5432` (PostgreSQL) are free on the host.
3. Environment file `.env` is present (copy from `.env.example`).

### 2.2 Standard Deployment Procedure
To deploy the stack locally with persistent storage:

```bash
# 1. Ensure .env is populated with safe defaults
cp .env.example .env    # Linux/macOS
# copy .env.example .env # Windows PowerShell

# 2. Pull verified images from Docker Hub and start services
docker compose pull
docker compose up -d

# 3. Verify container status
docker compose ps
```

### 2.3 Post-Deployment Smoke Verification
Run these validation commands to confirm operational readiness:

```bash
# Verify process liveness (HTTP 200)
curl -i http://localhost:8000/health/live

# Verify database readiness (HTTP 200)
curl -i http://localhost:8000/health/ready

# Verify metrics endpoint
curl -i http://localhost:8000/metrics

# Create a sample operational task
curl -X POST http://localhost:8000/api/v1/operations \
  -H "Content-Type: application/json" \
  -d '{"title": "Verify Deployment Runbook", "service_name": "apex-core", "status": "completed"}'
```

---

## 3. Safe Rollback Procedure

When an updated image release introduces regressions, unexpected 5xx spikes, or failing readiness checks, execute this standardized rollback procedure.

### 3.1 Rollback Trigger Criteria
Trigger an immediate rollback if:
- `/health/ready` returns HTTP 503 for more than 3 consecutive checks.
- Container restart count increases rapidly (`CrashLoopBackOff` equivalent).
- Error rate on `/api/v1/*` exceeds 5% of total requests over 3 minutes.

### 3.2 Executable Rollback Steps (3-Step Tag Swap)

```bash
# Step 1: Set the image tag back to the previous stable release or commit SHA
export APP_IMAGE_TAG=sha-626120f          # Linux/macOS
# $env:APP_IMAGE_TAG = "sha-626120f"     # Windows PowerShell

# Step 2: Pull target image & re-apply Docker Compose (zero-downtime container recreation)
docker compose pull apex-api
docker compose up -d apex-api

# Step 3: Verify the restored container passes readiness probe
curl -f http://localhost:8000/health/ready
```

*(Alternatively, run the automated helper script: `./scripts/rollback.sh sha-626120f` or `.\scripts\rollback.ps1 -TargetTag sha-626120f`)*

---

## 4. Incident Response & Alert Triage Playbooks

### Alert 1: `ApexDatabaseConnectivityLost`
- **Severity:** High / P1
- **Symptom:** `/health/ready` returns HTTP 503 (`"database": "disconnected"`).
- **Potential Causes:**
  1. PostgreSQL container terminated or unresponsive.
  2. Network partition on Docker bridge network `apex-network`.
  3. Connection pool saturation.
- **Triage & Remediation Steps:**
  1. Check database container status:
     ```bash
     docker compose ps apex-db
     ```
  2. Inspect database logs for crashes or out-of-memory kills:
     ```bash
     docker compose logs --tail=50 apex-db
     ```
  3. Test PostgreSQL readiness directly from host:
     ```bash
     docker compose exec apex-db pg_isready -U apex_user -d apex_ops_db
     ```
  4. If database hung, restart the database service:
     ```bash
     docker compose restart apex-db
     ```

### Alert 2: `ApexApiHigh5xxRate`
- **Severity:** High / P2
- **Symptom:** Upstream clients reporting HTTP 500 errors.
- **Triage & Remediation Steps:**
  1. Inspect structured JSON logs filtering for `level="ERROR"`:
     ```bash
     docker compose logs apex-api | grep '"level": "ERROR"'
     ```
  2. Extract the `request_id` from the error log to trace the exact request payload.
  3. If regression caused by new release, trigger Rollback Procedure (§3.2).

---

## 5. Troubleshooting & Diagnostics Playbook

### Diagnostic Commands Quick Reference

| Action | Command |
| :--- | :--- |
| **View live API logs** | `docker compose logs -f apex-api` |
| **View live DB logs** | `docker compose logs -f apex-db` |
| **Inspect container resources** | `docker stats` |
| **Check container port bindings** | `docker compose port apex-api 8000` |
| **Run test suite inside repo** | `pytest -v` |
| **Stop entire stack** | `docker compose down` |
| **Reset persistent database volume** | `docker compose down -v && docker compose up -d` |

### Common Error Resolutions

#### Problem: `Port 8000 already in use`
- **Diagnosis:** Another local process or previous container is holding port 8000.
- **Fix (Windows):** `netstat -ano | findstr :8000` followed by `taskkill /PID <PID> /F`.
- **Fix (Linux/Mac):** `lsof -i :8000` followed by `kill -9 <PID>`.

#### Problem: Container starts but healthcheck says `unhealthy`
- **Diagnosis:** The app process took longer than `start_period` (5s) or failed to connect to Postgres.
- **Fix:** View health check failure reason:
  ```bash
  docker inspect --format='{{json .State.Health}}' apex-api
  ```
