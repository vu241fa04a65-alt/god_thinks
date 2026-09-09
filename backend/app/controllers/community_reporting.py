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

@router.get("/trends")
def get_community_trends(
    location: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(CommunityTrend)
    if location:
        query = query.filter(CommunityTrend.location.ilike(f"%{location}%"))
    trends = query.order_by(CommunityTrend.count.desc()).limit(limit).all()

    total_reports = sum(t.count for t in trends)
    high_risk_zones = [t.location for t in trends if t.count >= 5]

    return {
        "status": "success",
        "total_reported_cases": total_reports,
        "active_regions_monitored": len(set(t.location for t in trends)),
        "high_risk_zones": list(set(high_risk_zones)),
        "aggregate_trends": [
            {
                "id": t.id,
                "disease_name": t.disease_name,
                "reported_cases": t.count,
                "location": t.location,
                "risk_level": "High" if t.count >= 10 else ("Moderate" if t.count >= 4 else "Low"),
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in trends
        ]
    }

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
