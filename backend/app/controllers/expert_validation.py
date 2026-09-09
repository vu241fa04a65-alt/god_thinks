from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import Report, User, RewardPoints, DiseasePrediction
from backend.app.models.schemas import ReportResponse, ReportValidationUpdate, ExpertValidateRequest
from backend.app.controllers.auth import get_current_user, get_optional_current_user
from backend.app.services.sms_service import sms_service

router = APIRouter(prefix="/expert", tags=["Expert Validation"])

@router.post("/validate")
def validate_prediction(
    validation_in: ExpertValidateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    valid_statuses = ["approved", "verified", "rejected"]
    norm_status = validation_in.status.lower().strip()
    if norm_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{validation_in.status}'. Must be one of: {valid_statuses}"
        )

    report = db.query(Report).filter(Report.id == validation_in.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with id {validation_in.report_id} not found")

    report.status = "verified" if norm_status in ["approved", "verified"] else "rejected"
    
    # If corrected disease provided, update prediction record
    if validation_in.corrected_disease:
        pred = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == report.id).first()
        if pred:
            pred.disease_name = validation_in.corrected_disease

    bonus_points = 0
    if report.status == "verified":
        bonus_points = 50
        bonus = RewardPoints(
            user_id=report.user_id,
            points=bonus_points,
            reason=f"Expert approved report #{report.id} ({report.crop_type})"
        )
        db.add(bonus)
        farmer = db.query(User).filter(User.id == report.user_id).first()
        if farmer:
            farmer.points += bonus_points

    db.commit()
    db.refresh(report)

    return {
        "status": "success",
        "message": f"Report #{report.id} prediction successfully marked as {report.status}",
        "report_id": report.id,
        "validation_status": report.status,
        "expert_notes": validation_in.expert_notes,
        "crop_type": report.crop_type,
        "farmer_id": report.user_id,
        "bonus_points_awarded": bonus_points
    }

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
