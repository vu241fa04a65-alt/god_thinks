from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.models.database import engine, Base
from backend.app.utils.logger import logger

# Import controllers
from backend.app.controllers.auth import router as auth_router
from backend.app.controllers.farmer_reports import router as reports_router
from backend.app.controllers.disease_detection import router as disease_router
from backend.app.controllers.community_reporting import router as community_router
from backend.app.controllers.gamification import router as gamification_router
from backend.app.controllers.expert_validation import router as expert_router

# Create DB tables
Base.metadata.create_all(bind=engine)
logger.info("Database schemas initialized.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="CropHealthAI RESTful API for Farmer Health Scouting, Disease Detection, and Community Gamification."
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(disease_router, prefix=settings.API_V1_STR)
app.include_router(community_router, prefix=settings.API_V1_STR)
app.include_router(gamification_router, prefix=settings.API_V1_STR)
app.include_router(expert_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {"status": "healthy", "service": "CropHealthAI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
