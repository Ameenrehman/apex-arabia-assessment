# Apex Operations API — Architectural Decision Memo
---

## 1. Executive Summary

This memorandum details the technical decisions, security measures, observability strategy, and cost-aware cloud hosting plan for the **Apex Operations API**. The solution prioritizes **reproducibility, simplicity, security hygiene, and transparent operational evidence** over unnecessary complexity, ensuring a reliable local-to-production lifecycle.

---

## 2. Core Architectural Decisions & Trade-Offs

### 2.1 Framework: Python FastAPI vs. Flask / Django
- **Decision:** Selected **FastAPI** with **Uvicorn** ASGI web server.
- **Rationale:** 
  - FastAPI provides native, automatic data validation via Pydantic, reducing boilerplate input parsing code.
  - Generates interactive OpenAPI/Swagger documentation (`/docs`) out of the box, simplifying cross-team testing and review.
  - Lightweight and asynchronous, making it ideal for low-latency operational tooling in AI and DevOps environments.
- **Trade-off:** Flask is slightly simpler for absolute trivial apps, but lacks native schema validation and automatic OpenAPI generation without third-party plugins. Django is excessively heavy for an API service.

### 2.2 Local Orchestration: Docker Compose vs. Local Kubernetes (Minikube/Kind)
- **Decision:** Selected **Docker Compose** with multi-stage container builds.
- **Rationale:**
  - Fast, reliable, and 100% reproducible on any developer laptop (Windows, macOS, Linux) with a single command (`docker compose up -d`).
  - Supports native container healthchecks (`pg_isready` for Postgres, `/health/ready` for API), dependency ordering (`condition: service_healthy`), and persistent named volumes.
  - Eliminates the steep overhead and hardware resource footprint of local Kubernetes clusters for a junior assessment.
- **Trade-off:** Does not simulate Kubernetes Ingress or StatefulSets, but offers identical container runtime behavior while maximizing reviewability.

### 2.3 Database: PostgreSQL vs. SQLite / In-Memory Mock
- **Decision:** Standardized on **PostgreSQL 16 Alpine** for local Docker Compose and **SQLite in-memory** for fast isolated unit testing.
- **Rationale:**
  - Real-world operations APIs require ACID transactions and real relational storage.
  - Demonstrates realistic connection pooling, network isolation, and failure recovery.
  - In-memory SQLite during test execution allows tests to complete in under 0.2 seconds with zero external dependencies.

---

## 3. Security & Configuration Hygiene

### 3.1 Non-Root Container Execution
- **Implementation:** The `Dockerfile` explicitly creates a dedicated non-root user and group:
  ```dockerfile
  RUN groupadd -g 10001 appgroup && \
      useradd -u 10001 -g appgroup -s /bin/bash -m appuser
  USER 10001:10001
  ```
- **Security Impact:** If a vulnerability is exploited within the application, the attacker is confined to an unprivileged container account without root capabilities or host escape vectors.

### 3.2 Secrets Management & Configuration Isolation
- **Rule:** Absolute zero hardcoded credentials in source code.
- **Implementation:**
  - `.gitignore` strictly excludes `.env` and all credential files.
  - `.env.example` provides a sanitized, fully documented template with safe development defaults.
  - Application settings are loaded and validated at runtime using `pydantic-settings`.

### 3.3 Least-Privilege Access Matrix

| Entity | Scope of Access | Granted Permissions | Justification |
| :--- | :--- | :--- | :--- |
| **API Container User** | Container filesystem | Read-only app code, write `/tmp` | Prevents file tampering |
| **Database User (`apex_user`)** | PostgreSQL | DDL & DML on `apex_ops_db` only | Cannot access system catalogs or postgres superuser |
| **CI/CD Runner** | GitHub Actions | `contents: read` | Minimum permission required to checkout code and build |
| **Cloud IAM Role (Target)** | AWS ECS Task | Read specific Secrets Manager ARN | Least privilege runtime access |

### 3.4 Dependency & Image Vulnerability Scanning
- **Static Code Analysis:** `ruff` enforces PEP 8 styling and imports.
- **Dependency Audit:** `pip-audit` checks Python dependencies against known CVE databases.
- **Container Scanning:** Aqua Security `Trivy` runs in the GitHub Actions CI pipeline to inspect base image layers and OS packages for High and Critical vulnerabilities.

---

## 4. Observability & Alerting Proposal

### 4.1 Structured JSON Logging & Correlation IDs
- Standard plain-text logs are difficult to parse in modern log aggregators.
- All logs in this project are emitted as **structured JSON objects** with standardized fields:
  `{"timestamp", "level", "logger", "message", "request_id", "method", "path", "status_code", "latency_ms"}`.
- Every HTTP request receives an `X-Request-ID` correlation UUID, enabling distributed tracing across log streams.

### 4.2 Proposed Alert Rules (Prometheus / Alertmanager)

| Alert Name | Condition | Severity | Description |
| :--- | :--- | :---: | :--- |
| **`ApexApiHigh5xxRate`** | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.02` | P1 (Critical) | >2% of requests returning 5xx server errors over 5 minutes |
| **`ApexDatabaseDisconnected`** | `apex_health_ready_status == 0` for 1m | P1 (Critical) | Readiness probe failing; database unreachable |
| **`ApexApiLatencyP95High`** | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5` | P2 (Warning) | 95th percentile latency exceeds 500ms |

---

## 5. Cost-Aware Path to Cloud Hosting ($20–$35 / Month)

To transition from local Docker Compose to cloud hosting sustainably, we propose a two-phase cost-optimized architecture:

```
[Route 53 / Cloudflare DNS]
           │
           ▼
[Application Load Balancer / HTTPS]
           │
           ▼
[AWS ECS Fargate Task (apex-api)] ──> [AWS RDS PostgreSQL (db.t4g.micro)]
  (0.25 vCPU, 0.5 GB RAM)                    (Multi-AZ optional for prod)
           │
           ▼
[AWS Secrets Manager / SSM Parameter Store]
```

### Monthly Cost Breakdown (Target: < $35/month)

| Component | Cloud Provider & Specification | Estimated Monthly Cost |
| :--- | :--- | :---: |
| **Container Compute** | AWS ECS Fargate (1 task: 0.25 vCPU, 0.5 GB RAM) | ~$8.50 / month |
| **Relational Database** | AWS RDS PostgreSQL `db.t4g.micro` (1-year reserved or single-AZ) | ~$14.00 / month |
| **Storage & Backups** | 20 GB gp3 SSD storage + automated snapshots | ~$2.50 / month |
| **Secrets & Networking** | AWS SSM Parameter Store (Standard tier: Free) + Data Transfer | ~$2.00 / month |
| **TOTAL ESTIMATED** | | **~$27.00 / month** |

*Alternative (Ultra-Low Cost):* DigitalOcean App Platform ($5/mo container + $15/mo managed database = **$20/month total**).

---

## 6. What I Would Improve With More Time

1. **Automated DB Migrations (Alembic):** Integrate Alembic into the startup lifecycle or CI pre-deploy hook to safely execute database schema migrations.
2. **Horizontal Autoscaling:** Add AWS ECS Target Tracking Policies or Kubernetes HPA based on CPU utilization and request counts.
3. **OpenTelemetry Tracing:** Upgrade correlation ID logging to full OpenTelemetry spans exported to Grafana Tempo or AWS X-Ray.
4. **Terraform IaC:** Codify cloud infrastructure (ECS, RDS, VPC) into reusable Terraform modules with remote state locking in S3/DynamoDB.
