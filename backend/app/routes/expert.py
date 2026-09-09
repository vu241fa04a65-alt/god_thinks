from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import Report, User, RewardPoints, DiseasePrediction
from backend.app.models.schemas import ExpertValidateRequest
from backend.app.routes.auth import get_optional_current_user
from backend.app.auth.dependencies import require_role
from backend.app.routes import success_envelope, error_envelope

router = APIRouter(prefix="/expert", tags=["Expert Validation"])


@router.post("/validate")
@require_role("expert")
def validate_prediction(
    validation_in: ExpertValidateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Validate crop disease report diagnosis.
    Role-enforced for 'expert' when authentication credentials are provided.
    """
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

    data = {
        "report_id": report.id,
        "validation_status": report.status,
        "expert_notes": validation_in.expert_notes,
        "crop_type": report.crop_type,
        "farmer_id": report.user_id,
        "bonus_points_awarded": bonus_points
    }
    return success_envelope(data=data)


@router.post("/review")
def expert_review(
    validation_in: ExpertValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("expert"))
):
    """
    Strictly role-guarded expert validation endpoint requiring verified 'expert' credentials.
    """
    return validate_prediction(validation_in=validation_in, db=db, current_user=current_user)
