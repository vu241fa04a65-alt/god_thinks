import json
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.models.database import get_db
from backend.app.models.entities import DiseasePrediction, User, RewardPoints, CommunityTrend, Report
from backend.app.models.schemas import DiseasePredictionResponse
from backend.app.controllers.auth import get_current_user
from backend.app.services.ml_inference import ml_service
from backend.app.services.translation_service import translation_service
from backend.app.utils.validation import validate_image_file
from backend.app.utils.logger import logger

router = APIRouter(prefix="/disease", tags=["Disease Detection"])

@router.post("/detect", response_model=DiseasePredictionResponse)
async def detect_disease(
    file: UploadFile = File(...),
    report_id: Optional[int] = Form(None),
    location: str = Form("General Region"),
    target_lang: str = Form("en"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_image_file(file)
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(f"Disease detection for user: {current_user.name} ({current_user.username})")
    prediction = ml_service.predict(content)

    # Prepare visual explanation overlay metadata (e.g., bounding boxes, lesion heatmap, treatment protocol)
    overlay_data = {
        "severity": prediction["severity"],
        "causes": prediction["causes"],
        "prevention": prediction["prevention"],
        "treatment": prediction["treatment"],
        "bounding_boxes": [{"x": 0.25, "y": 0.35, "width": 0.40, "height": 0.30, "label": prediction["disease_name"]}]
    }

    # Save DiseasePrediction
    record = DiseasePrediction(
        report_id=report_id,
        disease_name=prediction["disease_name"],
        confidence=prediction["confidence"],
        explanation_overlay=json.dumps(overlay_data)
    )
    db.add(record)

    # Award 20 points and update User points
    reward = RewardPoints(
        user_id=current_user.id,
        points=20,
        reason=f"Diagnosed {prediction['crop_name']} ({prediction['disease_name']})"
    )
    db.add(reward)
    current_user.points += 20

    # Update CommunityTrend for this disease & location
    trend = db.query(CommunityTrend).filter(
        CommunityTrend.disease_name == prediction["disease_name"],
        CommunityTrend.location == location
    ).first()
    if trend:
        trend.count += 1
    else:
        trend = CommunityTrend(
            disease_name=prediction["disease_name"],
            count=1,
            location=location
        )
        db.add(trend)

    db.commit()
    db.refresh(record)

    translated_disease = translation_service.translate(prediction["disease_name"], target_lang)

    return DiseasePredictionResponse(
        id=record.id,
        report_id=record.report_id,
        crop_name=prediction["crop_name"],
        disease_name=translated_disease,
        confidence=record.confidence,
        explanation_overlay=record.explanation_overlay,
        created_at=record.created_at,
        points_awarded=20
    )
