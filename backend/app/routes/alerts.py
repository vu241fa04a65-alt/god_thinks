import math
from typing import Optional, List, Dict, Any
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
