from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import DiseasePrediction, User, RewardPoints
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
    target_lang: str = Form("en"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_image_file(file)
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    logger.info(f"Processing disease detection for user {current_user.username}, image size: {len(content)} bytes")
    prediction = ml_service.predict(content)

    # Save to database
    record = DiseasePrediction(
        user_id=current_user.id,
        crop_name=prediction["crop_name"],
        disease_name=prediction["disease_name"],
        confidence=prediction["confidence"],
        severity=prediction["severity"],
        causes=prediction["causes"],
        prevention=prediction["prevention"],
        treatment=prediction["treatment"]
    )
    db.add(record)

    # Award 20 gamification points for active scouting
    points = RewardPoints(
        user_id=current_user.id,
        points=20,
        reason=f"Diagnosed {prediction['crop_name']} ({prediction['disease_name']})",
        transaction_type="earned"
    )
    db.add(points)
    db.commit()
    db.refresh(record)

    # Multilingual translation
    translated_disease = translation_service.translate(prediction["disease_name"], target_lang)
    translated_severity = translation_service.translate(prediction["severity"], target_lang)

    return DiseasePredictionResponse(
        id=record.id,
        crop_name=prediction["crop_name"],
        disease_name=translated_disease,
        confidence=prediction["confidence"],
        severity=translated_severity,
        causes=prediction["causes"],
        prevention=prediction["prevention"],
        treatment=prediction["treatment"],
        points_awarded=20
    )
