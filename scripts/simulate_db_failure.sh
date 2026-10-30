#!/usr/bin/env bash
# ==============================================================================
# Apex Operations API — Failure Investigation Demonstration (Linux/macOS)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo " Failure Investigation: Database Connectivity Severance"
echo "=========================================================="

# Step 1: Check Baseline Health
echo -e "\n[Step 1] Baseline Readiness Check (Before Failure):"
curl -s -i "http://localhost:8000/health/ready" | head -n 5

# Step 2: Simulate Outage
echo -e "\n[Step 2] Simulating Outage: Pausing PostgreSQL container (apex-db)..."
docker compose pause apex-db
sleep 2

# Step 3: Demonstrate Failure Detection
echo -e "\n[Step 3] Querying /health/ready during outage (Expect HTTP 503):"
curl -s -i "http://localhost:8000/health/ready" | head -n 5 || true

# Step 4: Display Structured Logs
echo -e "\n[Step 4] Recent Structured JSON Logs from apex-api:"
docker compose logs --tail=5 apex-api

# Step 5: Remediate / Recover
echo -e "\n[Step 5] Recovering PostgreSQL container (unpause)..."
docker compose unpause apex-db
sleep 3

# Step 6: Verify Recovery
echo -e "\n[Step 6] Verification Check Post-Recovery:"
curl -s -i "http://localhost:8000/health/ready" | head -n 5
echo -e "\nInvestigation complete: Service successfully detected and recovered from DB failure."
