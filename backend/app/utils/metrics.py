import time
from typing import Callable
from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

# ==============================================================================
# Prometheus Metric Definitions
# ==============================================================================

# HTTP Request Count
HTTP_REQUESTS_TOTAL = Counter(
    "crophealth_http_requests_total",
    "Total HTTP requests handled by the application",
    ["method", "endpoint", "status_code"]
)

# HTTP Request Duration
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "crophealth_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Active In-Flight Requests
HTTP_ACTIVE_REQUESTS = Gauge(
    "crophealth_http_active_requests",
    "Current active in-flight HTTP requests"
)

# ML Predictions Metric
DISEASE_PREDICTIONS_TOTAL = Counter(
    "crophealth_disease_predictions_total",
    "Total disease predictions processed by the ML engine",
    ["crop_type", "disease"]
)

# Expert Validations Metric
EXPERT_REVIEWS_TOTAL = Counter(
    "crophealth_expert_reviews_total",
    "Total expert agronomist reviews submitted",
    ["decision"]
)

# Outbreak Alert Broadcasts
ALERT_BROADCASTS_TOTAL = Counter(
    "crophealth_alert_broadcasts_total",
    "Total SMS outbreak broadcast alerts dispatched",
    ["severity"]
)

# Database Connection Health
DB_HEALTH_GAUGE = Gauge(
    "crophealth_database_healthy",
    "Database connectivity status (1 = healthy, 0 = degraded)"
)


# ==============================================================================
# Prometheus Middleware
# ==============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records HTTP latency, request count, and status code.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ignore metrics scraping endpoint itself to prevent skewing
        if request.url.path in ("/metrics", "/api/v1/metrics"):
            return await call_next(request)

        HTTP_ACTIVE_REQUESTS.inc()
        start_time = time.time()
        method = request.method
        path = request.url.path

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            raise
        finally:
            duration = time.time() - start_time
            HTTP_ACTIVE_REQUESTS.dec()

            # Normalize parameterized routes (avoid high-cardinality paths)
            normalized_path = path
            for prefix in ("/reports/", "/alerts/"):
                if path.startswith(prefix) and len(path.split("/")) > 2:
                    parts = path.split("/")
                    # replace integer IDs
                    normalized_parts = [":id" if p.isdigit() else p for p in parts]
                    normalized_path = "/".join(normalized_parts)
                    break

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=normalized_path,
                status_code=str(status_code)
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=normalized_path
            ).observe(duration)


# ==============================================================================
# Prometheus Metrics Router
# ==============================================================================

router = APIRouter(tags=["Observability"])

@router.get("/metrics", include_in_schema=False)
def metrics_endpoint():
    """
    Prometheus metrics scraping endpoint.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
