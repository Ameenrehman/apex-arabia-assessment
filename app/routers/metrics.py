"""Prometheus Metrics Exporter for Application Observability."""

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

router = APIRouter(tags=["Metrics & Monitoring"])

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "apex_http_requests_total",
    "Total count of HTTP requests processed by Apex Operations API",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "apex_http_request_duration_seconds",
    "Histogram of HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)


@router.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Exposes application telemetry and RED metrics (Rate, Errors, Duration) in Prometheus text format.",
)
def prometheus_metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
