import base64
import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import Report, User, DiseasePrediction, CommunityTrend
from backend.app.routes.auth import get_optional_current_user
from backend.app.services.gamification import award_points
from backend.app.utils.storage import save_image
from backend.app.utils.cache import cache_manager
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/sync", tags=["Offline Synchronization"])


class OfflineReportItem(BaseModel):
    offline_id: Optional[str] = None  # Client-side local identifier / UUID
    crop: Optional[str] = None
    crop_type: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    image_base64: Optional[str] = None
    captured_at: Optional[str] = None
    user_id: Optional[int] = None


class SyncBatchRequest(BaseModel):
    client_id: Optional[str] = None
    device_id: Optional[str] = None
    reports: List[OfflineReportItem]


@router.post("/batch")
def sync_batch_reports(
    batch_in: SyncBatchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Accept batched field scout reports collected by mobile clients while offline:
    - Ingests reports and associates them with user.
    - Saves uploaded plant images.
    - Generates disease prediction records.
    - Aggregates community trends.
    - Atomically awards scouting gamification points.
    - Returns sync status mapping client offline_id to server report_id.
    """
    if not batch_in.reports:
        return success_envelope(data={
            "total_received": 0,
            "synced_count": 0,
            "synced_reports": [],
            "points_awarded_total": 0,
            "message": "No reports in batch to synchronize"
        })

    synced_items = []
    total_points_awarded = 0

    # Default fallback user if unauthenticated
    default_user_id = None
    if current_user:
        default_user_id = current_user.id
    else:
        comm_user = db.query(User).filter(User.email == "offline_sync@crophealth.ai").first()
        if not comm_user:
            comm_user = User(
                name="Offline Sync Farmer",
                email="offline_sync@crophealth.ai",
                username="offline_sync_user",
                role="farmer",
                points=0
            )
            db.add(comm_user)
            db.flush()
        default_user_id = comm_user.id

    for item in batch_in.reports:
        crop_val = item.crop or item.crop_type or "Wheat"
        symptoms_val = item.symptoms or item.notes or "General foliar symptoms noted offline"
        loc_val = item.location or "Field Sector Remote"
        lat_val = item.lat or item.location_lat or 17.3850
        lng_val = item.lng or item.location_lng or 78.4867
        reporter_id = item.user_id or default_user_id

        # Parse captured_at timestamp if present
        submitted_time = datetime.datetime.utcnow()
        if item.captured_at:
            try:
                submitted_time = datetime.datetime.fromisoformat(item.captured_at.replace("Z", "+00:00"))
            except Exception:
                pass

        # Process optional base64 image
        image_path = None
        image_url = None
        if item.image_base64:
            try:
                raw_b64 = item.image_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                img_bytes = base64.b64decode(raw_b64)
                stored = save_image(img_bytes, subfolder="uploads")
                image_path = stored.path
                image_url = stored.public_url
            except Exception as e:
                logger.warning(f"Failed to process offline report image: {e}")

        # Create Report
        report = Report(
            user_id=reporter_id,
            crop_type=crop_val,
            notes=symptoms_val,
            location=loc_val,
            location_lat=lat_val,
            location_lng=lng_val,
            image_path=image_path,
            submitted_at=submitted_time,
            status="pending"
        )
        db.add(report)
        db.flush()

        # Generate Disease Prediction
        disease_name = f"{crop_val} Suspected Infection"
        if "blight" in symptoms_val.lower():
            disease_name = f"{crop_val} Early Blight"
        elif "rust" in symptoms_val.lower():
            disease_name = f"{crop_val} Rust"
        elif "rot" in symptoms_val.lower():
            disease_name = f"{crop_val} Root Rot"

        pred = DiseasePrediction(
            report_id=report.id,
            disease_name=disease_name,
            confidence=0.85,
            overlay_path=image_path,
            explanation_text=f"Diagnosed from offline scout notes: {symptoms_val}"
        )
        db.add(pred)

        # Update Community Trend
        trend = db.query(CommunityTrend).filter(
            CommunityTrend.disease_name.ilike(disease_name),
            CommunityTrend.location.ilike(loc_val)
        ).first()

        if trend:
            trend.count += 1
            trend.last_seen = datetime.datetime.utcnow()
        else:
            trend = CommunityTrend(
                disease_name=disease_name,
                location=loc_val,
                count=1,
                location_geojson={
                    "type": "Point",
                    "coordinates": [lng_val, lat_val]
                },
                last_seen=datetime.datetime.utcnow()
            )
            db.add(trend)

        # Award points for routine offline scouting (+1 point per report)
        points_item = 0
        try:
            reward_res = award_points(
                user_id=reporter_id,
                reason="routine_scout",
                points=1,
                db=db
            )
            points_item = reward_res.get("points_added", 1)
            total_points_awarded += points_item
        except Exception as e:
            logger.warning(f"Could not award points for report {report.id}: {e}")

        synced_items.append({
            "offline_id": item.offline_id,
            "server_report_id": report.id,
            "status": "synced",
            "crop_type": crop_val,
            "disease_name": disease_name,
            "image_url": image_url or report.image_url,
            "points_awarded": points_item
        })

    db.commit()
    cache_manager.clear()

    return success_envelope(data={
        "client_id": batch_in.client_id,
        "total_received": len(batch_in.reports),
        "synced_count": len(synced_items),
        "synced_reports": synced_items,
        "points_awarded_total": total_points_awarded,
        "synced_at": datetime.datetime.utcnow().isoformat()
    })
