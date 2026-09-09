from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import Report, User, RewardPoints
from backend.app.models.schemas import ReportCreate, ReportResponse
from backend.app.controllers.auth import get_current_user
from backend.app.utils.validation import validate_coordinates

router = APIRouter(prefix="/reports", tags=["Farmer Reports"])

@router.post("/", response_model=ReportResponse)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_coordinates(report_in.location_lat, report_in.location_lon)

    report = Report(
        user_id=current_user.id,
        title=report_in.title,
        crop_name=report_in.crop_name,
        description=report_in.description,
        location_lat=report_in.location_lat,
        location_lon=report_in.location_lon,
        status="pending"
    )
    db.add(report)

    # Award 15 reward points for submitting a field report
    reward = RewardPoints(
        user_id=current_user.id,
        points=15,
        reason=f"Submitted crop health report: {report_in.title}",
        transaction_type="earned"
    )
    db.add(reward)

    db.commit()
    db.refresh(report)
    return report

@router.get("/my-reports", response_model=List[ReportResponse])
def get_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.created_at.desc()).all()

@router.get("/{report_id}", response_model=ReportResponse)
def get_report_details(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
