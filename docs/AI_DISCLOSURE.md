# AI Assistance Disclosure Statement

---

## 1. Compliance Statement

In strict adherence to the assessment guidelines (*"AI assistance is permitted but must be disclosed with specific uses. State assumptions and trade-offs"*), this document outlines the exact nature and scope of AI tools utilized during the preparation of this submission.

---

## 2. Tools Used

- **Gemini 3.8 Flash** and **Claude Code** (used for syntax assistance, drafting documentation, and brainstorming test scenarios).

---

## 3. Specific Scope of AI Utilization

### 3.1 What AI Was Used For:
1. **Boilerplate Scaffolding:** Accelerated the initial drafting of standard Python FastAPI routes, Pydantic validation schemas, and SQLAlchemy ORM class definitions.
2. **Test Scenario Brainstorming:** Formulated realistic edge-case testing scenarios (e.g., simulating database connection loss and intentional failure tripwires for CI gating).
3. **Documentation Structure & ASCII Diagrams:** Assisted in drafting structured Markdown templates, tables, and ASCII network topology diagrams for `RUNBOOK.md` and `DECISION_MEMO.md`.

### 3.2 What Was Designed, Verified, and Executed by the Candidate:

1. **Dockerfile Engineering:** Designed the multi-stage build (`builder` vs `runner`), configured non-root system user (`appuser` UID 10001), and set up the `/health/live` container healthcheck probe.
2. **Docker Compose Orchestration:** Configured `docker-compose.yml` with PostgreSQL 16, persistent storage volume (`apex_postgres_data`), internal network isolation, resource limits, and health dependency (`depends_on: condition: service_healthy`).
3. **CI/CD Pipeline Stages:** Built the GitHub Actions pipeline stages:
   - Stage 1: Code Linting (Ruff)
   - Stage 2: Automated Tests (6 Pytest checks with coverage)
   - Stage 3: Security & Vulnerability Scan (Trivy)
   - Stage 4: Gated Container Build & Push to Docker Hub (`ameen2607/apex-arabia`)
   - Added path filtering (`paths:`) and manual trigger (`workflow_dispatch`).
4. **Security & Secrets Hygiene:** Enforced non-root least privilege, sanitized `.env.example`, `.gitignore` secrets policy, and CVE image scanning.
5. **Release & Rollback Strategy:** Designed the 3-step image tag rollback procedure and created PowerShell/Bash rollback scripts.
6. **Hands-on Local Verification:** Manually executed, tested, and validated all Docker containers, endpoints, Swagger UI, failure simulation, and test suites on a local machine.

---

## 4. Key Assumptions & Trade-Offs

- **Assumption 1:** A local Docker Compose environment backed by PostgreSQL represents an authentic and sufficient simulation of containerized production operations for a Junior DevOps Engineer assessment.
- **Assumption 2:** Using in-memory SQLite for test execution isolates the CI test runner from database provisioning latency, enabling sub-second test execution without compromising integration validity.
- **Assumption 3:** A manual-first, 3-step rollback procedure via Docker Compose environment tag swapping provides clearer reviewability and lower operational risk than opaque custom shell scripts.
