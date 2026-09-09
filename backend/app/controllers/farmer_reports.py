from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from backend.app.models.entities import Report, User, RewardPoints, DiseasePrediction, CommunityTrend
from backend.app.models.schemas import ReportCreate, ReportResponse
from backend.app.controllers.auth import get_current_user, get_optional_current_user
from backend.app.services.ml_inference import ml_service

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
    
    # 1. Read and validate image
    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # 2. Run ML inference
    try:
        prediction_result = ml_service.predict(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    detected_crop = crop_type or prediction_result.get("crop_name", "Tomato")
    disease_name = prediction_result.get("disease_name", "Tomato Early Blight")
    confidence = prediction_result.get("confidence", 0.92)

    # 3. Associate with user or guest farmer
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

    # 4. Save Report
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

    # 5. Save Disease Prediction with explanation overlay
    overlay_desc = f"Grad-CAM Heatmap overlay identifying symptomatic lesions on {detected_crop} ({disease_name})"
    prediction_record = DiseasePrediction(
        report_id=report.id,
        disease_name=disease_name,
        confidence=confidence,
        explanation_overlay=overlay_desc
    )
    db.add(prediction_record)

    # 6. Aggregate Community Trend
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

    # 7. Reward points for scout upload
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
    db.refresh(prediction_record)

    advisory = get_treatment_advisory(disease_name, detected_crop)

    return {
        "status": "success",
        "message": "Report uploaded and analyzed successfully",
        "report_id": report.id,
        "crop_type": report.crop_type,
        "location": report.location,
        "image_url": report.image_url,
        "status_review": report.status,
        "disease_prediction": {
            "id": prediction_record.id,
            "disease_name": prediction_record.disease_name,
            "confidence": prediction_record.confidence,
            "severity": prediction_result.get("severity", "Moderate"),
            "explanation_overlay": prediction_record.explanation_overlay
        },
        "treatment_advisory": advisory,
        "points_awarded": points_awarded
    }

@router.post("/", response_model=ReportResponse)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = Report(
        user_id=current_user.id,
        crop_type=report_in.crop_type,
        image_url=report_in.image_url,
        location=report_in.location,
        status="pending"
    )
    db.add(report)

    reward = RewardPoints(
        user_id=current_user.id,
        points=15,
        reason=f"Submitted crop report for {report_in.crop_type} at {report_in.location}"
    )
    db.add(reward)
    current_user.points += 15

    db.commit()
    db.refresh(report)
    return report

@router.get("/my-reports", response_model=List[ReportResponse])
def get_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.created_at.desc()).all()

@router.get("/{report_id}")
def get_report_details(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report with id {report_id} not found")

    pred = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == report.id).first()
    disease_name = pred.disease_name if pred else "Undetermined"
    advisory = get_treatment_advisory(disease_name, report.crop_type)

    return {
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
