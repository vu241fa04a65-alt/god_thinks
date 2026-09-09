import os
import tempfile
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.disease_prediction import DiseasePrediction
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/ml", tags=["ML Inference"])


@router.post("/infer")
async def infer_disease(
    file: UploadFile = File(...),
    report_id: Optional[int] = Form(None),
    confidence_threshold: Optional[float] = Form(0.25),
    db: Session = Depends(get_db)
):
    """
    Accept image file, save to temporary path, run ML inference with Grad-CAM explainability,
    persist a DiseasePrediction database record, and return diagnosis with bounding boxes,
    mask polygons, and XAI overlay.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No valid image file uploaded")

    # Read uploaded bytes
    try:
        image_bytes = await file.read()
        if not image_bytes or len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded image is empty")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image stream: {str(e)}")

    # Write to a secure temporary file
    temp_suffix = os.path.splitext(file.filename)[1] or ".jpg"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix)
    temp_path = temp_file.name
    try:
        temp_file.write(image_bytes)
        temp_file.flush()
        temp_file.close()

        # Import inference pipeline
        from ml_model.inference import predict

        logger.info(f"Executing ML inference on uploaded image '{file.filename}' with conf_threshold={confidence_threshold}")
        prediction_result = predict(temp_path, conf_threshold=confidence_threshold or 0.25)

        # Persist DiseasePrediction in Database
        db_prediction = DiseasePrediction(
            report_id=report_id,
            disease_name=prediction_result.get("disease_name", "Unknown Foliar Anomaly"),
            confidence=float(prediction_result.get("confidence", 0.0)),
            overlay_path=prediction_result.get("overlay_image_path") or prediction_result.get("backend_overlay_path"),
            explanation_text=prediction_result.get("explanation_text")
        )
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        response_data = {
            "prediction_id": db_prediction.id,
            "report_id": db_prediction.report_id,
            "disease_name": db_prediction.disease_name,
            "confidence": db_prediction.confidence,
            "confidence_threshold": prediction_result.get("confidence_threshold", confidence_threshold),
            "top_predictions": prediction_result.get("top_predictions", []),
            "heatmap_base64": prediction_result.get("heatmap_base64"),
            "explanation_text": db_prediction.explanation_text,
            "visual_cues": prediction_result.get("visual_cues"),
            "infected_regions": prediction_result.get("infected_regions", []),
            "overlay_image_path": prediction_result.get("overlay_image_path"),
            "backend_overlay_path": prediction_result.get("backend_overlay_path"),
            "crop_name": prediction_result.get("crop_name"),
            "severity": prediction_result.get("severity")
        }

        return success_envelope(response_data)

    except Exception as e:
        logger.error(f"Inference error in /ml/infer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Inference pipeline execution error: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
