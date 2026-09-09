from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.database import get_db
from backend.app.models.entities import Report, DiseasePrediction
from backend.app.models.schemas import ReportResponse

router = APIRouter(prefix="/community", tags=["Community Reporting"])

@router.get("/feed", response_model=List[ReportResponse])
def get_community_feed(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()

@router.get("/outbreaks")
def get_outbreak_hotspots(db: Session = Depends(get_db)):
    hotspots = (
        db.query(
            DiseasePrediction.crop_name,
            DiseasePrediction.disease_name,
            func.count(DiseasePrediction.id).label("count")
        )
        .group_by(DiseasePrediction.crop_name, DiseasePrediction.disease_name)
        .order_by(func.count(DiseasePrediction.id).desc())
        .limit(5)
        .all()
    )

    return [
        {
            "crop": h.crop_name,
            "disease": h.disease_name,
            "reported_cases": h.count,
            "risk_level": "High" if h.count > 10 else "Moderate"
        }
        for h in hotspots
    ]
