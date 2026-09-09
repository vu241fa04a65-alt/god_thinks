from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.utils.logger import logger
from backend.app.routes import success_envelope, error_envelope

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
    application = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        description="CropHealthAI RESTful API for Farmer Health Scouting, Disease Detection, and Community Gamification.",
        lifespan=lifespan
    )

    # CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
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

    # Health Endpoints
    @application.get("/health")
    @application.get(f"{settings.API_V1_STR}/health")
    def health_check():
        return success_envelope(data={
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT
        })

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
        ml_router
    ]

    for r in routers:
        application.include_router(r, prefix=settings.API_V1_STR)
        application.include_router(r)

    return application

# Default App Instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
