"""Apex Operations API — Main Application Entrypoint.

Provides operations management, container health/readiness probes,
and structured observability.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.logging_config import CorrelationIdMiddleware, setup_logging
from app.routers import health, metrics, operations

# Configure structured JSON logging
logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.APP_ENV} mode"
    )
    # Automatically initialize tables if database is available
    try:
        init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.warning(
            f"Could not initialize database on startup (will be verified via /health/ready): {exc}"
        )

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Operational task tracking and container readiness API for Apex AI Arabia.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register observability and correlation ID middleware
app.add_middleware(CorrelationIdMiddleware)

# Register routers
app.include_router(health.router)
app.include_router(operations.router)
app.include_router(metrics.router)


@app.get(
    "/",
    tags=["Root"],
    summary="API Index",
    description="Returns service metadata, version, and links to documentation.",
)
def api_root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "documentation": "/docs",
        "health": {
            "liveness": "/health/live",
            "readiness": "/health/ready",
            "metrics": "/metrics",
        },
    }
