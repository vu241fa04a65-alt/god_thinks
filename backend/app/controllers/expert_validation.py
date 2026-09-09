from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import Report, User, RewardPoints
from backend.app.models.schemas import ReportResponse, ReportValidationUpdate
from backend.app.controllers.auth import get_current_user
from backend.app.services.sms_service import sms_service

router = APIRouter(prefix="/expert", tags=["Expert Validation"])

@router.get("/pending-reviews", response_model=List[ReportResponse])
def get_pending_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only experts or admins can review
    if current_user.role not in ["expert", "admin"]:
        raise HTTPException(status_code=403, detail="Expert privileges required.")
    return db.query(Report).filter(Report.status == "pending").all()

@router.post("/validate/{report_id}", response_model=ReportResponse)
def validate_report(
    report_id: int,
    validation: ReportValidationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["expert", "admin"]:
        raise HTTPException(status_code=403, detail="Expert privileges required.")

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = validation.status
    report.expert_notes = validation.expert_notes

    # If verified, award 50 bonus points to farmer
    if validation.status == "verified":
        bonus = RewardPoints(
            user_id=report.user_id,
            points=50,
            reason=f"Expert validated your report #{report.id} ({report.crop_type})"
        )
        db.add(bonus)
        if report.user:
            report.user.points += 50

        # Send SMS alert to farmer if phone number registered
        if report.user and report.user.phone_number:
            sms_service.send_alert(
                to_phone=report.user.phone_number,
                message=f"CropHealthAI: Your report for {report.crop_type} has been verified by an expert!"
            )

    db.commit()
    db.refresh(report)
    return report
