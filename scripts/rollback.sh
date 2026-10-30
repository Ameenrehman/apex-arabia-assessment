#!/usr/bin/env bash
# ==============================================================================
# Apex Operations API — Safe Rollback Procedure (Linux/macOS)
# ==============================================================================
# Usage:
#   ./scripts/rollback.sh [sha-626120f]
# ==============================================================================
set -euo pipefail

TARGET_TAG="${1:-sha-626120f}"

echo "=========================================================="
echo " Initiating Safe Rollback Procedure -> Tag: ${TARGET_TAG}"
echo "=========================================================="

# Step 1: Export Target Image Tag
export APP_IMAGE_TAG="${TARGET_TAG}"
echo "[1/3] Configured APP_IMAGE_TAG to ${TARGET_TAG}"

# Step 2: Pull target image & re-apply Docker Compose
echo "[2/3] Pulling image ${TARGET_TAG} from Docker Hub and re-applying..."
docker compose pull apex-api
docker compose up -d apex-api

# Step 3: Verify Service Health & Readiness Probe
echo "[3/3] Verifying service readiness on http://localhost:8000/health/ready..."
sleep 3

if curl -s -f "http://localhost:8000/health/ready" | grep -q '"status":"ready"'; then
    echo "SUCCESS: Rollback to ${TARGET_TAG} verified! Service is healthy."
else
    echo "ERROR: Health check probe failed during rollback!"
    exit 1
fi
