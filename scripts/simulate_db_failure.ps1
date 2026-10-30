# ==============================================================================
# Apex Operations API — Failure Investigation Demonstration (Windows PowerShell)
# ==============================================================================
# Demonstrates:
# 1. Healthy state (HTTP 200)
# 2. Simulated database outage (HTTP 503 Service Unavailable)
# 3. Structured log capture showing error diagnostics
# 4. Service recovery (HTTP 200 restored)
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Failure Investigation: Database Connectivity Severance" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Step 1: Check Baseline Health
Write-Host "`n[Step 1] Baseline Readiness Check (Before Failure):" -ForegroundColor Yellow
try {
    $baseline = Invoke-RestMethod -Uri "http://localhost:8000/health/ready" -Method Get
    Write-Host "Status: HTTP 200 OK -> $($baseline | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "Could not query API. Is 'docker compose up -d' running?" -ForegroundColor Red
    exit 1
}

# Step 2: Simulate Outage by pausing PostgreSQL container
Write-Host "`n[Step 2] Simulating Outage: Pausing PostgreSQL container (apex-db)..." -ForegroundColor Yellow
docker compose pause apex-db

Start-Sleep -Seconds 2

# Step 3: Demonstrate Failure Detection via Readiness Probe
Write-Host "`n[Step 3] Querying /health/ready during outage (Expect HTTP 503):" -ForegroundColor Yellow
try {
    $outage = Invoke-WebRequest -Uri "http://localhost:8000/health/ready" -Method Get -SkipHttpErrorCheck
    Write-Host "Received HTTP $($outage.StatusCode) -> $($outage.Content)" -ForegroundColor Red
} catch {
    Write-Host "Error captured as expected: $_" -ForegroundColor Red
}

# Step 4: Display Structured Error Log from API container
Write-Host "`n[Step 4] Recent Structured JSON Logs from apex-api:" -ForegroundColor Yellow
docker compose logs --tail=5 apex-api

# Step 5: Remediate / Recover Database
Write-Host "`n[Step 5] Recovering PostgreSQL container (unpause)..." -ForegroundColor Yellow
docker compose unpause apex-db

Start-Sleep -Seconds 3

# Step 6: Verify Recovery
Write-Host "`n[Step 6] Verification Check Post-Recovery:" -ForegroundColor Yellow
try {
    $recovered = Invoke-RestMethod -Uri "http://localhost:8000/health/ready" -Method Get
    Write-Host "Status: HTTP 200 OK -> $($recovered | ConvertTo-Json -Compress)" -ForegroundColor Green
    Write-Host "`nInvestigation complete: Service successfully detected and recovered from DB failure." -ForegroundColor Cyan
} catch {
    Write-Host "Recovery verification failed: $_" -ForegroundColor Red
}
