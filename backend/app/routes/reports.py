from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import Report, User, RewardPoints, DiseasePrediction, CommunityTrend
from backend.app.routes.auth import get_current_user, get_optional_current_user
from backend.app.services.ml_service import ml_service
from backend.app.routes import success_envelope, error_envelope

router = APIRouter(prefix="/reports", tags=["Farmer Reports"])

ADVISORY_MAP = {
    "Tomato Early Blight": {
        "causes": "Alternaria solani fungal pathogen spreading via splash droplets during warm, humid conditions.",
        "prevention": "Rotate crops with non-solanaceous plants for 2-3 years, stake plants, and water at soil level.",
        "treatment": "Apply copper octanoate or azoxystrobin spray at first sign. Prune affected bottom leaves."
    },
    "Tomato Late Blight": {
        "causes": "Phytophthora infestans oomycete water mold thriving in cool, damp weather.",
        "prevention": "Ensure wide spacing for canopy airflow and plant certified disease-free seedlings.",
        "treatment": "Spray chlorothalonil, mancozeb, or metalaxyl immediately. Remove severely diseased vines."
    },
    "Potato Early Blight": {
        "causes": "Alternaria solani attacking maturing foliage during tuber formation.",
        "prevention": "Maintain balanced soil nitrogen and potassium levels, irrigate in the early morning.",
        "treatment": "Apply Mancozeb or systemic triazole fungicides upon initial lesion sighting."
    },
    "Apple Scab": {
        "causes": "Venturia inaequalis fungus producing olive-green velvety lesions.",
        "prevention": "Rake and compost fallen leaves, prune canopy to maximize sunlight penetration.",
        "treatment": "Apply sulfur or captan fungicides during early leaf and bud emergence."
    },
    "Corn Common Rust": {
        "causes": "Puccinia sorghi fungus causing reddish-brown pustules on leaf blades.",
        "prevention": "Plant resistant hybrid seed varieties and ensure balanced nitrogen fertilizing.",
        "treatment": "Apply fungicides containing pyraclostrobin or propiconazole if rust occurs before silking."
    },
    "Grape Black Rot": {
        "causes": "Guignardia bidwellii fungus causing dark circular lesions and shriveled fruit mummies.",
        "prevention": "Prune infected canes in dormant season, train vines to maximize sun and air exposure.",
        "treatment": "Apply myclobutanil or mancozeb sprays starting at early shoot growth."
    }
}

def get_treatment_advisory(disease_name: str, crop_type: str) -> dict:
    for key, advisory in ADVISORY_MAP.items():
        if key.lower() in disease_name.lower():
            return advisory
    return {
        "causes": f"Suspected foliar pathogen affecting {crop_type} under elevated humidity conditions.",
        "prevention": "Ensure proper crop row aeration, avoid wetting foliage, and prune infected leaves.",
        "treatment": "Apply copper-based bio-fungicide or neem oil extract spray."
    }

@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    crop_type: Optional[str] = Form(None),
    location: Optional[str] = Form("Sector 4 - Farm Node"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Run ML Inference
    try:
        prediction_result = ml_service.predict(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    detected_crop = crop_type or prediction_result.get("crop_name", "Tomato")
    disease_name = prediction_result.get("disease_name", "Tomato Early Blight")
    confidence = prediction_result.get("confidence", 0.92)

    # Associate with user or guest farmer
    if current_user:
        user_id = current_user.id
    else:
        guest_user = db.query(User).filter(User.username == "guest_farmer").first()
        if not guest_user:
            guest_user = User(
                name="Guest Farmer",
                username="guest_farmer",
                email="guest@crophealth.local",
                hashed_password="guest",
                role="farmer",
                points=0
            )
            db.add(guest_user)
            db.commit()
            db.refresh(guest_user)
        user_id = guest_user.id

    # Create Report
    image_url = f"/uploads/{file.filename}"
    report = Report(
        user_id=user_id,
        crop_type=detected_crop,
        image_url=image_url,
        location=location or "Field Node Alpha",
        status="pending"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Save Disease Prediction
    overlay_desc = f"Grad-CAM Heatmap overlay identifying lesions for {disease_name} (Confidence: {int(confidence * 100)}%)"
    pred_record = DiseasePrediction(
        report_id=report.id,
        disease_name=disease_name,
        confidence=confidence,
        explanation_overlay=overlay_desc
    )
    db.add(pred_record)

    # Update CommunityTrend
    loc_str = location or "Field Node Alpha"
    trend = db.query(CommunityTrend).filter(
        CommunityTrend.disease_name == disease_name,
        CommunityTrend.location == loc_str
    ).first()
    if trend:
        trend.count += 1
    else:
        trend = CommunityTrend(
            disease_name=disease_name,
            location=loc_str,
            count=1
        )
        db.add(trend)

    # Reward points
    points_awarded = 0
    if current_user:
        points_awarded = 20
        reward = RewardPoints(
            user_id=current_user.id,
            points=points_awarded,
            reason=f"Uploaded crop scout report #{report.id} ({disease_name})"
        )
        db.add(reward)
        current_user.points += points_awarded

    db.commit()
    db.refresh(pred_record)

    advisory = get_treatment_advisory(disease_name, detected_crop)

    data = {
        "report_id": report.id,
        "crop_type": report.crop_type,
        "location": report.location,
        "image_url": report.image_url,
        "status": report.status,
        "disease_prediction": {
            "id": pred_record.id,
            "disease_name": pred_record.disease_name,
            "confidence": pred_record.confidence,
            "severity": prediction_result.get("severity", "Moderate"),
            "explanation_overlay": pred_record.explanation_overlay
        },
        "treatment_advisory": advisory,
        "points_awarded": points_awarded
    }
    return success_envelope(data=data)

@router.post("/")
def create_report(
    report_in: dict,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user_id = current_user.id if current_user else 1
    report = Report(
        user_id=user_id,
        crop_type=report_in.get("crop_type", "Tomato"),
        image_url=report_in.get("image_url"),
        location=report_in.get("location", "Farm Field"),
        status="pending"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return success_envelope(data={
        "id": report.id,
        "user_id": report.user_id,
        "crop_type": report.crop_type,
        "image_url": report.image_url,
        "location": report.location,
        "status": report.status,
        "created_at": report.created_at.isoformat() if report.created_at else None
    })

@router.get("/list")
def list_reports(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    crop_type: Optional[str] = Query(None, description="Filter by crop type"),
    status: Optional[str] = Query(None, description="Filter by report status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    query = db.query(Report)
    if crop_type:
        query = query.filter(Report.crop_type.ilike(f"%{crop_type}%"))
    if status:
        query = query.filter(Report.status == status)
    if user_id:
        query = query.filter(Report.user_id == user_id)

    total_count = query.count()
    offset = (page - 1) * limit
    reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()

    data = {
        "total": total_count,
        "page": page,
        "limit": limit,
        "items": [
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
    }
    return success_envelope(data=data)

@router.get("/{report_id}")
def get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with id {report_id} not found")

    pred = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == report.id).first()
    disease_name = pred.disease_name if pred else "Undetermined"
    advisory = get_treatment_advisory(disease_name, report.crop_type)

    data = {
        "report": {
            "id": report.id,
            "user_id": report.user_id,
            "crop_type": report.crop_type,
            "image_url": report.image_url,
            "location": report.location,
            "status": report.status,
            "created_at": report.created_at.isoformat() if report.created_at else None
        },
        "disease_prediction": {
            "id": pred.id if pred else None,
            "disease_name": disease_name,
            "confidence": pred.confidence if pred else 0.0,
            "explanation_overlay": pred.explanation_overlay if pred else None
        } if pred else None,
        "treatment_advisory": advisory
    }
    return success_envelope(data=data)
