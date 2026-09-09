import math
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import User
from backend.app.models.schemas import SMSAlertRequest
from backend.app.services.notification_service import notification_service
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/alerts", tags=["Notifications & Alerts"])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


@router.post("/sms")
def send_sms_alert(
    alert_in: SMSAlertRequest,
    db: Session = Depends(get_db)
):
    """
    Dispatch SMS alert:
    1. Direct phone dispatch: validates number, respects user opt-in preferences, and throttles spam.
    2. Geo-fenced outbreak dispatch: broadcasts outbreak alerts to all subscribed farmers in a geo-fence.
    """
    msg = alert_in.message.strip()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert message content cannot be empty"
        )
    if len(msg) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert message exceeds 500 characters limit"
        )

    # 1. Direct Phone Number Dispatch
    if alert_in.phone_number and alert_in.phone_number.strip():
        phone = alert_in.phone_number.strip()

        # Check user opt-in preference if user exists in database
        user = db.query(User).filter(User.phone == phone).first()
        if user and not user.sms_opt_in:
            return {
                "status": "skipped",
                "recipient": phone,
                "message": "User has opted out of SMS notifications",
                "sms_opt_in": False
            }

        try:
            dispatch_result = notification_service.send_sms(to_phone=phone, message=msg)
            return {
                "status": "success",
                "message": "SMS alert successfully processed",
                "recipient": phone,
                "delivery_details": dispatch_result
            }
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {e}")
            raise HTTPException(status_code=500, detail=f"SMS Gateway Error: {str(e)}")

    # 2. Geo-Fence Outbreak Broadcast Dispatch
    center_lat = alert_in.lat or (alert_in.geo_fence.lat if alert_in.geo_fence else None)
    center_lng = alert_in.lng or alert_in.lon or (alert_in.geo_fence.lng if alert_in.geo_fence else None)
    radius_km = alert_in.radius_km or (alert_in.geo_fence.radius_km if alert_in.geo_fence else 25.0)

    if center_lat is not None and center_lng is not None:
        # Query farmers who have phone numbers and have opted-in to SMS
        eligible_users = (
            db.query(User)
            .filter(
                User.phone.isnot(None),
                User.phone != "",
                User.sms_opt_in == True
            )
            .all()
        )

        matched_recipients = []
        for u in eligible_users:
            # Check user coordinates against geo-fence
            u_lat = u.location_lat
            u_lng = u.location_lng
            if u_lat is not None and u_lng is not None:
                dist = haversine_distance(center_lat, center_lng, u_lat, u_lng)
                if dist <= radius_km:
                    matched_recipients.append(u.phone)
            else:
                # Include user if no coordinates set (broadcast policy for sector)
                matched_recipients.append(u.phone)

        # De-duplicate recipients
        unique_recipients = list(set(matched_recipients))

        # Enqueue SMS broadcast asynchronously
        queue_result = notification_service.queue_sms(
            message=msg,
            recipients=unique_recipients
        )

        return {
            "status": "success",
            "message": f"Geo-fenced outbreak alerts enqueued for {len(unique_recipients)} subscribed farmers",
            "geo_fence": {
                "lat": center_lat,
                "lng": center_lng,
                "radius_km": radius_km
            },
            "matched_users_count": len(unique_recipients),
            "queued_recipients": unique_recipients,
            "queue_details": queue_result
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either 'phone_number' or geo-fence coordinates ('lat' and 'lng' / 'geo_fence') must be provided"
    )


class AlertSubscriptionRequest(BaseModel):
    phone: str
    preferred_language: Optional[str] = "en"  # en, hi, mr, te
    geofence_radius_km: Optional[float] = 25.0
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    user_id: Optional[int] = None


class AlertUnsubscribeRequest(BaseModel):
    phone: str
    user_id: Optional[int] = None


@router.post("/subscribe")
def subscribe_to_alerts(
    req: AlertSubscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Subscribe a farmer to hyper-local SMS outbreak alerts:
    - Validates phone number format.
    - Sets preferred language, location, and geo-fence perimeter.
    - Sends an immediate confirmation SMS with an opt-in code via notification_service.
    """
    clean_phone = req.phone.strip().replace(" ", "").replace("-", "")
    # Basic phone validation (min 10 digits)
    digits = [c for c in clean_phone if c.isdigit()]
    if len(digits) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mobile number format. Please provide a valid 10+ digit mobile number."
        )

    # Standardize international format if needed
    if not clean_phone.startswith("+"):
        if len(digits) == 10:
            clean_phone = f"+91{clean_phone}"
        else:
            clean_phone = f"+{clean_phone}"

    # Generate 6-digit opt-in verification code
    import random
    opt_in_code = f"{random.randint(100000, 999999)}"

    # Check if user exists, otherwise update or create
    user = None
    if req.user_id:
        user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        user = db.query(User).filter(User.phone == clean_phone).first()

    if user:
        user.phone = clean_phone
        user.sms_opt_in = True
        user.preferred_language = req.preferred_language or user.preferred_language
        user.geofence_radius_km = req.geofence_radius_km or 25.0
        if req.location:
            user.location = req.location
        if req.lat is not None:
            user.location_lat = req.lat
        if req.lng is not None:
            user.location_lng = req.lng
    else:
        user = User(
            name="Field Farmer",
            phone=clean_phone,
            sms_opt_in=True,
            preferred_language=req.preferred_language or "en",
            geofence_radius_km=req.geofence_radius_km or 25.0,
            location=req.location or "Farm Field",
            location_lat=req.lat or 17.3850,
            location_lng=req.lng or 78.4867,
            role="farmer",
            points=0
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Send confirmation SMS with opt-in code
    lang = user.preferred_language.lower()
    if lang == "hi":
        confirm_msg = (
            f"नमस्ते! CropHealthAI अलर्ट में आपका स्वागत है। आपका पुष्टिकरण कोड है: {opt_in_code}। "
            f"आपको {user.geofence_radius_km}km के दायरे में फसल रोग अलर्ट प्राप्त होंगे।"
        )
    elif lang == "mr":
        confirm_msg = (
            f"नमस्कार! CropHealthAI अलर्ट सेवेत आपले स्वागत आहे. आपला कोड: {opt_in_code}. "
            f"आपल्याला {user.geofence_radius_km}km परिसरातील पीक रोग सूचना मिळतील."
        )
    elif lang == "te":
        confirm_msg = (
            f"నమస్కారం! CropHealthAI హెచ్చరికలకు స్వాగతం. మీ కోడ్: {opt_in_code}. "
            f"మీకు {user.geofence_radius_km}km పరిధిలోని పంట తెగులు సమాచారం అందుతుంది."
        )
    else:
        confirm_msg = (
            f"Welcome to CropHealthAI Outbreak Alerts! Your verification code is {opt_in_code}. "
            f"You are subscribed to alerts within a {user.geofence_radius_km}km geo-fence."
        )

    sms_result = None
    try:
        sms_result = notification_service.send_sms(to_phone=clean_phone, message=confirm_msg, bypass_throttle=True)
    except Exception as e:
        logger.warning(f"Could not dispatch subscription confirmation SMS to {clean_phone}: {e}")

    return success_envelope(data={
        "user_id": user.id,
        "phone": clean_phone,
        "sms_opt_in": True,
        "preferred_language": user.preferred_language,
        "geofence_radius_km": user.geofence_radius_km,
        "location": user.location,
        "opt_in_code": opt_in_code,
        "confirmation_dispatched": sms_result is not None and sms_result.get("status") in ["sent", "simulated", "queued"],
        "message": f"Successfully subscribed {clean_phone} to crop outbreak alerts"
    })


@router.post("/unsubscribe")
def unsubscribe_from_alerts(
    req: AlertUnsubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe a farmer from SMS outbreak notifications.
    """
    clean_phone = req.phone.strip().replace(" ", "").replace("-", "")
    user = None
    if req.user_id:
        user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        user = db.query(User).filter(User.phone == clean_phone).first()

    if not user:
        # Check standard prefix
        if not clean_phone.startswith("+"):
            user = db.query(User).filter(User.phone == f"+91{clean_phone}").first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription for {req.phone} not found"
        )

    user.sms_opt_in = False
    db.commit()
    db.refresh(user)

    return success_envelope(data={
        "user_id": user.id,
        "phone": user.phone,
        "sms_opt_in": False,
        "message": "You have been unsubscribed from CropHealthAI SMS alerts"
    })


@router.get("/status")
def get_alert_status(
    phone: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Query alert subscription preferences for a phone number or user.
    """
    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif phone:
        clean_phone = phone.strip()
        user = db.query(User).filter(User.phone == clean_phone).first()
        if not user and not clean_phone.startswith("+"):
            user = db.query(User).filter(User.phone == f"+91{clean_phone}").first()

    if not user:
        return success_envelope(data={
            "subscribed": False,
            "sms_opt_in": False,
            "preferred_language": "en",
            "geofence_radius_km": 25.0
        })

    return success_envelope(data={
        "user_id": user.id,
        "phone": user.phone,
        "subscribed": user.sms_opt_in,
        "sms_opt_in": user.sms_opt_in,
        "preferred_language": user.preferred_language,
        "geofence_radius_km": user.geofence_radius_km,
        "location": user.location
    })


@router.post("/opt-in")
def update_sms_opt_in(
    user_id: int,
    opt_in: bool,
    db: Session = Depends(get_db)
):
    """
    Update a user's SMS alert subscription preference (Opt-In / Opt-Out).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    user.sms_opt_in = opt_in
    db.commit()
    db.refresh(user)

    return success_envelope(data={
        "user_id": user.id,
        "name": user.name,
        "phone": user.phone,
        "sms_opt_in": user.sms_opt_in,
        "message": "SMS subscription preferences updated successfully"
    })
