# ==============================================================================
# Apex Operations API — Deployment Script (Windows PowerShell)
# ==============================================================================
# Usage:
#   .\scripts\deploy.ps1 [-TargetTag latest]
# ==============================================================================

param (
    [string]$TargetTag = "latest"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Deploying Apex Operations API -> Tag: $TargetTag" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[1/4] .env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "[1/4] Found existing .env configuration." -ForegroundColor Green
}

# Step 2: Configure target image tag
$env:APP_IMAGE_TAG = $TargetTag
Write-Host "[2/4] Configured APP_IMAGE_TAG to $TargetTag" -ForegroundColor Yellow

# Step 3: Pull verified images from Docker Hub
Write-Host "[3/4] Pulling images from Docker Hub..." -ForegroundColor Yellow
docker compose pull

# Step 4: Start services in background
Write-Host "[4/4] Starting containers with Docker Compose..." -ForegroundColor Yellow
docker compose up -d

# Smoke test verification
Write-Host "Waiting for service readiness..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health/ready" -Method Get -TimeoutSec 5
    if ($response.status -eq "ready") {
        Write-Host "==========================================================" -ForegroundColor Green
        Write-Host " SUCCESS: Deployment of $TargetTag completed!" -ForegroundColor Green
        Write-Host " - Swagger UI:    http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host " - Health Probe:  http://localhost:8000/health/ready" -ForegroundColor Cyan
        Write-Host " - Metrics:       http://localhost:8000/metrics" -ForegroundColor Cyan
        Write-Host "==========================================================" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: Service started, but readiness check failed: $_" -ForegroundColor Yellow
    Write-Host "Check logs with: docker compose logs apex-api" -ForegroundColor Yellow
}
