"""Structured JSON Logging & Observability Middleware.

Formats all application logs as structured JSON records and enriches
HTTP requests with unique correlation IDs (X-Request-ID).
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class JSONFormatter(logging.Formatter):
    """Custom JSON log formatter for structured observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include contextual fields if present
        for field in ("request_id", "method", "path", "status_code", "latency_ms", "client_ip"):
            if hasattr(record, field):
                log_record[field] = getattr(record, field)

        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured JSON logging on the root logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Remove existing handlers to avoid duplicate lines
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers if needed
    logging.getLogger("uvicorn.access").handlers = []
    return logging.getLogger("apex.ops.api")


logger = logging.getLogger("apex.ops.api")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a correlation ID (X-Request-ID) to each request

    and logs the structured request lifecycle with timing metrics.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Attach correlation ID to outgoing response header
            response.headers["X-Request-ID"] = request_id

            # Log completed request in structured JSON format
            logger.info(
                f"HTTP {request.method} {request.url.path} responded {response.status_code} in {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "latency_ms": duration_ms,
                    "client_ip": client_ip,
                },
            )
            raise exc
