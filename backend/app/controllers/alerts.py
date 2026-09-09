from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import SMSAlertRequest
from backend.app.services.sms_service import sms_service

router = APIRouter(prefix="/alerts", tags=["Notifications & Alerts"])

@router.post("/sms")
def send_sms_alert(alert_in: SMSAlertRequest):
    phone = alert_in.phone_number.strip()
    msg = alert_in.message.strip()

    if not phone:
        raise HTTPException(status_code=400, detail="Phone number cannot be empty")
    if not msg:
        raise HTTPException(status_code=400, detail="Alert message content cannot be empty")
    if len(msg) > 500:
        raise HTTPException(status_code=400, detail="Alert message exceeds 500 characters limit")

    try:
        dispatch_result = sms_service.send_alert(to_phone=phone, message=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMS Gateway Error: {str(e)}")

    return {
        "status": "success",
        "message": "SMS alert successfully processed",
        "recipient": phone,
        "delivery_details": dispatch_result
    }
