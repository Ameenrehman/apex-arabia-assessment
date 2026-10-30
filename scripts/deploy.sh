#!/usr/bin/env bash
# ==============================================================================
# Apex Operations API — Deployment Script (Linux/macOS)
# ==============================================================================
# Usage:
#   ./scripts/deploy.sh [latest | sha-xxxxxxx | v1.0.0]
# ==============================================================================
set -euo pipefail

TARGET_TAG="${1:-latest}"

echo "=========================================================="
echo " Deploying Apex Operations API -> Tag: ${TARGET_TAG}"
echo "=========================================================="

# Step 1: Ensure .env exists
if [ ! -f .env ]; then
    echo "[1/4] .env not found. Creating from .env.example..."
    cp .env.example .env
else
    echo "[1/4] Found existing .env configuration."
fi

# Step 2: Configure target image tag
export APP_IMAGE_TAG="${TARGET_TAG}"
echo "[2/4] Configured APP_IMAGE_TAG to ${TARGET_TAG}"

# Step 3: Pull verified images from Docker Hub
echo "[3/4] Pulling images from Docker Hub..."
docker compose pull

# Step 4: Start services in background
echo "[4/4] Starting containers with Docker Compose..."
docker compose up -d

# Smoke test verification
echo "Waiting for service readiness..."
sleep 4

if curl -s -f "http://localhost:8000/health/ready" | grep -q '"status":"ready"'; then
    echo "=========================================================="
    echo " SUCCESS: Deployment of ${TARGET_TAG} completed!"
    echo " - Swagger UI:    http://localhost:8000/docs"
    echo " - Health Probe:  http://localhost:8000/health/ready"
    echo " - Metrics:       http://localhost:8000/metrics"
    echo "=========================================================="
else
    echo "WARNING: Service started, but readiness probe check did not return ready yet."
    echo "Check logs with: docker compose logs apex-api"
fi
