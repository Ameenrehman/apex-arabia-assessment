# ==============================================================================
# Apex Operations API — Safe Rollback Procedure (Windows PowerShell)
# ==============================================================================
# Usage:
#   .\scripts\rollback.ps1 [-TargetTag sha-626120f]
# ==============================================================================

param (
    [string]$TargetTag = "sha-626120f"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " initiating Safe Rollback Procedure -> Tag: $TargetTag" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Export Target Image Tag
$env:APP_IMAGE_TAG = $TargetTag
Write-Host "[1/3] Configured APP_IMAGE_TAG to $TargetTag" -ForegroundColor Yellow

# Step 2: Pull target image & re-apply Docker Compose with zero-downtime container recreation
Write-Host "[2/3] Pulling image $TargetTag from Docker Hub and re-applying..." -ForegroundColor Yellow
docker compose pull apex-api
docker compose up -d apex-api

# Step 3: Verify Service Health & Readiness Probe
Write-Host "[3/3] Verifying service readiness on http://localhost:8000/health/ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health/ready" -Method Get -TimeoutSec 5
    if ($response.status -eq "ready") {
        Write-Host "SUCCESS: Rollback to $TargetTag verified! Service is healthy." -ForegroundColor Green
    } else {
        Write-Host "WARNING: Service responded, but status is not ready: $($response | ConvertTo-Json)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: Health check probe failed during rollback: $_" -ForegroundColor Red
    exit 1
}
