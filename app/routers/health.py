"""Health & Readiness endpoints for container orchestrators and load balancers."""

from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import check_database_connection
from app.schemas import HealthLiveResponse, HealthReadyResponse

router = APIRouter(prefix="/health", tags=["Health & Observability"])


@router.get(
    "/live",
    response_model=HealthLiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Probe",
    description="Checks whether the application process is running. Used by Docker/Kubernetes to decide whether to restart the container.",
)
def liveness_probe() -> HealthLiveResponse:
    return HealthLiveResponse(
        status="alive",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=HealthReadyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Service is ready to handle traffic"},
        503: {"description": "Database dependency unreachable"},
    },
    summary="Readiness Probe",
    description="Verifies that the application can communicate with its persistent database. Used by load balancers before routing traffic.",
)
def readiness_probe():
    is_db_connected = check_database_connection()

    if is_db_connected:
        return HealthReadyResponse(
            status="ready",
            database="connected",
            timestamp=datetime.now(timezone.utc),
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "database": "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
