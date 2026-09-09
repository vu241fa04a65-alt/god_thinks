import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import (
    Report,
    User,
    DiseasePrediction,
    CommunityTrend,
    ExpertAction
)
from backend.app.models.schemas import ExpertValidateRequest
from backend.app.routes.auth import get_optional_current_user
from backend.app.auth.dependencies import require_role
from backend.app.services.gamification import award_points
from backend.app.services.notification_service import notification_service
from backend.app.utils.storage import generate_public_url
from backend.app.utils.cache import cache_manager
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/expert", tags=["Expert Portal & Validation"])


@router.get("/pending")
def get_pending_predictions(
    crop_type: Optional[str] = Query(None, description="Filter by crop type"),
    limit: int = Query(20, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    List pending disease prediction reports awaiting expert agronomist review,
    including uploaded plant images and explainable AI overlays.
    """
    query = db.query(Report).filter(Report.status == "pending")
    if crop_type:
        query = query.filter(Report.crop_type.ilike(f"%{crop_type}%"))

    total = query.count()
    reports = query.order_by(Report.submitted_at.desc()).offset(offset).limit(limit).all()

    items = []
    for r in reports:
        reporter_info = None
        if r.user:
            reporter_info = {
                "id": r.user.id,
                "name": r.user.name,
                "email": r.user.email,
                "phone": r.user.phone,
                "role": r.user.role
            }

        # Fetch predictions and heatmaps
        preds = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == r.id).all()
        predictions_data = [
            {
                "id": p.id,
                "disease_name": p.disease_name,
                "confidence": p.confidence,
                "overlay_path": p.overlay_path,
                "overlay_url": generate_public_url(p.overlay_path) if p.overlay_path else None,
                "explanation_text": p.explanation_text,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in preds
        ]

        items.append({
            "report_id": r.id,
            "id": r.id,
            "crop_type": r.crop_type,
            "image_path": r.image_path,
            "image_url": generate_public_url(r.image_path) if r.image_path else r.image_url,
            "location": r.location,
            "location_lat": r.location_lat,
            "location_lng": r.location_lng,
            "status": r.status,
            "notes": r.notes,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "reporter": reporter_info,
            "predictions": predictions_data
        })

    return success_envelope(data={
        "total": total,
        "limit": limit,
        "offset": offset,
        "pending_reports": items
    })


@router.post("/validate")
@require_role("expert")
def validate_prediction(
    validation_in: ExpertValidateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Expert validation workflow:
    - Decision: approve | reject (or status: approved | rejected | verified)
    - On approval:
      * report.status = validated
      * award points to reporter (+5 pts from rules engine)
      * increment community trend counts
    - On rejection:
      * report.status = rejected
      * store expert notes
      * notify reporter via SMS/email
    - Persists audit trail in expert_actions table.
    """
    raw_decision = (validation_in.decision or validation_in.status or "").lower().strip()
    valid_decisions = ["approve", "approved", "verified", "reject", "rejected"]
    if raw_decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision '{raw_decision}'. Must be one of: approve, reject (or approved, rejected, verified)"
        )

    is_approval = raw_decision in ["approve", "approved", "verified"]
    resolved_notes = validation_in.notes or validation_in.expert_notes or ""

    report = db.query(Report).filter(Report.id == validation_in.report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with id {validation_in.report_id} not found"
        )

    # 1. Update Report Status
    report.status = "validated" if is_approval else "rejected"
    if resolved_notes:
        if is_approval:
            report.notes = f"{report.notes or ''} [Expert Note: {resolved_notes}]".strip()
        else:
            report.notes = f"{report.notes or ''} [Expert Rejection: {resolved_notes}]".strip()

    # 2. Update corrected disease if specified
    active_disease = None
    if validation_in.corrected_disease:
        active_disease = validation_in.corrected_disease
        pred = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == report.id).first()
        if pred:
            pred.disease_name = validation_in.corrected_disease
    else:
        pred = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == report.id).first()
        active_disease = pred.disease_name if pred else f"{report.crop_type} Disorder"

    # 3. Resolve Expert ID for Audit Trail
    expert_id = current_user.id if current_user else None
    if not expert_id:
        # Check if an expert user exists in DB
        expert_user = db.query(User).filter(User.role == "expert").first()
        if expert_user:
            expert_id = expert_user.id

    points_awarded = 0
    community_trend_updated = False
    notification_result = None

    if is_approval:
        # 4a. Award Points to Reporter (+5 points for validated report rule)
        if report.user_id:
            try:
                reward_res = award_points(
                    user_id=report.user_id,
                    reason="validated_report",
                    points=5,
                    db=db
                )
                points_awarded = reward_res.get("points_added", 5)
            except Exception as e:
                logger.warning(f"Could not award points to reporter {report.user_id}: {e}")

        # 4b. Increment Community Trend Counts
        trend_location = report.location or "Field Sector Alpha"
        trend = db.query(CommunityTrend).filter(
            CommunityTrend.disease_name.ilike(active_disease),
            CommunityTrend.location.ilike(trend_location)
        ).first()

        if trend:
            trend.count += 1
            trend.last_seen = datetime.datetime.utcnow()
        else:
            trend = CommunityTrend(
                disease_name=active_disease,
                location=trend_location,
                count=1,
                location_geojson={
                    "type": "Point",
                    "coordinates": [report.location_lng or 78.4867, report.location_lat or 17.3850]
                },
                last_seen=datetime.datetime.utcnow()
            )
            db.add(trend)

        community_trend_updated = True
        cache_manager.clear()
    else:
        # 4c. On Rejection: Notify Reporter via SMS/email
        farmer = db.query(User).filter(User.id == report.user_id).first()
        if farmer:
            notification_result = notification_service.notify_reporter(
                user_phone=farmer.phone,
                user_email=farmer.email,
                report_id=report.id,
                crop_type=report.crop_type,
                decision="rejected",
                notes=resolved_notes
            )

    # 5. Persist Audit Trail in expert_actions Table
    audit_action = ExpertAction(
        expert_id=expert_id,
        report_id=report.id,
        decision="approved" if is_approval else "rejected",
        notes=resolved_notes,
        created_at=datetime.datetime.utcnow()
    )
    db.add(audit_action)

    db.commit()
    db.refresh(report)
    db.refresh(audit_action)

    data = {
        "report_id": report.id,
        "decision": "approved" if is_approval else "rejected",
        "status": report.status,
        "validation_status": "verified" if (is_approval and raw_decision in ["approved", "verified"]) else ("validated" if is_approval else "rejected"),
        "expert_id": expert_id,
        "action_id": audit_action.id,
        "expert_notes": resolved_notes,
        "notes": resolved_notes,
        "crop_type": report.crop_type,
        "farmer_id": report.user_id,
        "points_awarded": points_awarded,
        "community_trend_updated": community_trend_updated,
        "notification": notification_result
    }
    return success_envelope(data=data)


@router.get("/actions")
def get_expert_audit_trail(
    report_id: Optional[int] = Query(None, description="Filter by report id"),
    limit: int = Query(50, ge=1, le=100, description="Max audit entries"),
    db: Session = Depends(get_db)
):
    """
    Query the expert_actions audit trail table.
    """
    query = db.query(ExpertAction)
    if report_id:
        query = query.filter(ExpertAction.report_id == report_id)

    actions = query.order_by(ExpertAction.created_at.desc()).limit(limit).all()
    items = [
        {
            "id": a.id,
            "expert_id": a.expert_id,
            "report_id": a.report_id,
            "decision": a.decision,
            "notes": a.notes,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in actions
    ]
    return success_envelope(data={"total": len(items), "audit_actions": items})


@router.post("/review")
def expert_review(
    validation_in: ExpertValidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("expert"))
):
    """Strictly role-guarded expert review endpoint."""
    return validate_prediction(validation_in=validation_in, db=db, current_user=current_user)
