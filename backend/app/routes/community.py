from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import CommunityTrend, Report
from backend.app.routes import success_envelope, error_envelope

router = APIRouter(prefix="/community", tags=["Community & Surveillance"])

@router.get("/feed")
def get_community_feed(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()
    items = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "crop_type": r.crop_type,
            "image_url": r.image_url,
            "location": r.location,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reports
    ]
    return success_envelope(data=items)

@router.get("/trends")
def get_community_trends(
    location: Optional[str] = Query(None, description="Filter by location"),
    limit: int = Query(10, ge=1, le=50, description="Limit results"),
    db: Session = Depends(get_db)
):
    query = db.query(CommunityTrend)
    if location:
        query = query.filter(CommunityTrend.location.ilike(f"%{location}%"))
    trends = query.order_by(CommunityTrend.count.desc()).limit(limit).all()

    total_reports = sum(t.count for t in trends)
    high_risk_zones = list(set([t.location for t in trends if t.count >= 5]))

    data = {
        "total_reported_cases": total_reports,
        "active_regions_monitored": len(set(t.location for t in trends)),
        "high_risk_zones": high_risk_zones,
        "trends": [
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
    return success_envelope(data=data)

@router.get("/nearby")
def get_nearby_reports(
    lat: float = Query(17.3850, ge=-90.0, le=90.0, description="User latitude"),
    lon: float = Query(78.4867, ge=-180.0, le=180.0, description="User longitude"),
    radius_km: float = Query(25.0, ge=1.0, le=500.0, description="Search radius in km"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    # Simulated geo-spatial query returning nearby reported disease events
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()

    items = []
    for r in reports:
        items.append({
            "report_id": r.id,
            "crop_type": r.crop_type,
            "location": r.location,
            "distance_km": round(5.2 + (r.id % 12) * 1.5, 1),
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    data = {
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "nearby_reports_count": len(items),
        "reports": items
    }
    return success_envelope(data=data)
