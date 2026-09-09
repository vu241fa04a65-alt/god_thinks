from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import Report, CommunityTrend
from backend.app.models.schemas import ReportResponse, CommunityTrendResponse

router = APIRouter(prefix="/community", tags=["Community Reporting"])

@router.get("/feed", response_model=List[ReportResponse])
def get_community_feed(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()

@router.get("/trends", response_model=List[CommunityTrendResponse])
def get_community_trends(
    location: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(CommunityTrend)
    if location:
        query = query.filter(CommunityTrend.location.ilike(f"%{location}%"))
    return query.order_by(CommunityTrend.count.desc()).limit(limit).all()

@router.get("/outbreaks")
def get_outbreak_hotspots(db: Session = Depends(get_db)):
    trends = db.query(CommunityTrend).order_by(CommunityTrend.count.desc()).limit(10).all()
    return [
        {
            "disease": t.disease_name,
            "location": t.location,
            "reported_cases": t.count,
            "risk_level": "High" if t.count > 10 else "Moderate"
        }
        for t in trends
    ]
