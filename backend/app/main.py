from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.utils.logger import logger
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.metrics import PrometheusMiddleware, router as metrics_router, DB_HEALTH_GAUGE

# Initialize Sentry Error Tracking if DSN is configured
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,
        )
        logger.info(f"Sentry SDK initialized successfully for environment: {settings.ENVIRONMENT}")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry SDK: {e}")

# Import Route Modules
from backend.app.routes.auth import router as auth_router
from backend.app.routes.reports import router as reports_router
from backend.app.routes.expert import router as expert_router
from backend.app.routes.community import router as community_router
from backend.app.routes.gamification import router as gamification_router
from backend.app.controllers.disease_detection import router as disease_router
from backend.app.routes.weather import router as weather_router
from backend.app.controllers.alerts import router as alerts_router
from backend.app.routes.ml_proxy import router as ml_router
from backend.app.routes.sync import router as sync_router
from backend.app.routes.advisory import router as advisory_router
from backend.app.routes.chatbot import router as chatbot_router
from backend.app.auth import (
    AuthAuditMiddleware,
    SecurityHeadersMiddleware,
    GlobalRateLimitMiddleware
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    logger.info("CropHealthAI Backend initializing database schemas and services...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas ready. Application online.")
    yield
    # Shutdown event
    logger.info("CropHealthAI Backend shutting down cleanly...")

def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    tags_metadata = [
        {"name": "Auth", "description": "Authentication, JWT tokens, user registration, role enforcement, and login protection."},
        {"name": "Reports", "description": "Farmer crop scout reporting, image uploads, thumbnails, and cloud storage."},
        {"name": "Expert", "description": "Agronomist portal for reviewing, approving, rejecting predictions, and audit trail logs."},
        {"name": "Community", "description": "Surveillance, outbreak trends, GeoJSON clustering, and nearby report queries."},
        {"name": "Gamification", "description": "Reward points, activity ledger, reward claim catalog, and leaderboards."},
        {"name": "Weather Risk", "description": "Hyper-local weather risk forecasting and crop disease susceptibility models."},
        {"name": "Advisory", "description": "Integrated pest management recommendations, biological controls, and chemical restrictions."},
        {"name": "Alerts", "description": "SMS outbreak broadcast alerts to subscribed farmers within geo-fenced perimeters."},
        {"name": "Sync", "description": "Offline-first batch synchronization for field scouts and low-connectivity devices."},
        {"name": "ML Inference", "description": "Explainable AI pipeline with Grad-CAM heatmaps, bounding boxes, and visual cues."},
        {"name": "Health", "description": "Service health checks and uptime monitoring."}
    ]

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        openapi_tags=tags_metadata,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        description="CropHealthAI RESTful API for Farmer Health Scouting, Disease Detection, and Community Gamification.",
        lifespan=lifespan
    )

    # Defensive Security Headers & HTTPS Enforcement Middleware
    application.add_middleware(SecurityHeadersMiddleware)

    # API-wide Rate Limiting Middleware
    application.add_middleware(
        GlobalRateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE
    )

    # Security & Auth Audit Middleware
    application.add_middleware(AuthAuditMiddleware)

    # Prometheus Metrics Tracking Middleware
    application.add_middleware(PrometheusMiddleware)

    # CORS Whitelist Middleware
    cors_origins = settings.get_cors_origins()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Global Exception Handlers enforcing consistent response envelope
    @application.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(message=exc.detail, code=exc.status_code)
        )

    @application.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(message=exc.detail, code=exc.status_code)
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_envelope(message="Validation error", code=422, details=exc.errors())
        )

    @application.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=error_envelope(message=str(exc), code=500)
        )

    # Health & Readiness Probes for Containerized Deployments
    @application.get("/health")
    @application.get(f"{settings.API_V1_STR}/health")
    def health_check():
        """Liveness probe: verifies process is alive and responding."""
        return success_envelope(data={
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0"
        })

    @application.get("/ready")
    @application.get(f"{settings.API_V1_STR}/ready")
    def readiness_check():
        """Readiness probe: verifies database connectivity and storage volume status."""
        import os
        from sqlalchemy import text
        from backend.app.database import engine
        from backend.app.utils.storage import STORAGE_DIR

        checks = {
            "database": "degraded",
            "storage": "degraded"
        }
        is_ready = True

        # 1. Database connection check
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["database"] = "ready"
            DB_HEALTH_GAUGE.set(1)
        except Exception as e:
            is_ready = False
            checks["database"] = f"unhealthy: {str(e)}"
            DB_HEALTH_GAUGE.set(0)

        # 2. Storage write accessibility check
        try:
            if os.path.exists(STORAGE_DIR) and os.access(STORAGE_DIR, os.W_OK):
                checks["storage"] = "ready"
            else:
                is_ready = False
                checks["storage"] = "unwritable"
        except Exception as e:
            is_ready = False
            checks["storage"] = f"unhealthy: {str(e)}"

        if is_ready:
            return success_envelope(data={"status": "ready", "checks": checks})
        return JSONResponse(
            status_code=503,
            content=error_envelope(message="Service Not Ready", code=503, details=checks)
        )

    @application.get("/")
    def root():
        return success_envelope(data={
            "status": "online",
            "service": settings.PROJECT_NAME,
            "docs_url": "/docs",
            "api_v1": settings.API_V1_STR
        })

    # Register all routes with /api/v1 prefix and root prefix
    routers = [
        auth_router,
        reports_router,
        expert_router,
        community_router,
        gamification_router,
        disease_router,
        weather_router,
        alerts_router,
        ml_router,
        sync_router,
        advisory_router,
        chatbot_router,
        metrics_router
    ]

    for r in routers:
        application.include_router(r, prefix=settings.API_V1_STR)
        application.include_router(r)

    # Static file serving for stored images, overlays, and thumbnails
    from backend.app.utils.storage import STORAGE_DIR, UPLOADS_DIR
    application.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")
    application.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

    return application

# Default App Instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
