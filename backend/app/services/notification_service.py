import threading
from collections import deque
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.utils.logger import logger

class NotificationService:
    """
    Notification service managing Twilio SMS delivery with queue support.
    """
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        self.client = None
        self.queue = deque()
        self.lock = threading.Lock()

        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS Client successfully initialized in NotificationService.")
            except Exception as e:
                logger.warning(f"Twilio initialization note: {e}")

    def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Direct dispatch of SMS alert."""
        if self.client and self.from_phone:
            try:
                msg = self.client.messages.create(
                    body=message,
                    from_=self.from_phone,
                    to=to_phone
                )
                logger.info(f"SMS dispatched to {to_phone} via Twilio, SID: {msg.sid}")
                return {"status": "sent", "sid": msg.sid, "recipient": to_phone}
            except Exception as e:
                logger.error(f"Twilio delivery error: {e}")

        # Simulated fallback dispatch
        logger.info(f"[SIMULATED SMS] To: {to_phone} | Msg: {message}")
        return {"status": "simulated", "recipient": to_phone, "message": message}

    def enqueue_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Enqueue SMS notification for background/batch dispatch."""
        with self.lock:
            item = {"to_phone": to_phone, "message": message, "queued_at": "now"}
            self.queue.append(item)
            qsize = len(self.queue)
        logger.info(f"Enqueued SMS for {to_phone}. Queue depth: {qsize}")
        return {"status": "enqueued", "queue_position": qsize, "recipient": to_phone}

    def process_queue(self) -> List[Dict[str, Any]]:
        """Drain and dispatch queued SMS messages."""
        results = []
        with self.lock:
            batch = list(self.queue)
            self.queue.clear()

        for item in batch:
            res = self.send_sms(to_phone=item["to_phone"], message=item["message"])
            results.append(res)
        return results

    def send_email(self, to_email: str, subject: str, content: str) -> Dict[str, Any]:
        """Dispatch or simulate email notification."""
        logger.info(f"[EMAIL DISPATCH] To: {to_email} | Subject: {subject} | Content: {content[:100]}...")
        return {
            "status": "sent",
            "channel": "email",
            "recipient": to_email,
            "subject": subject
        }

    def notify_reporter(
        self,
        user_phone: Optional[str] = None,
        user_email: Optional[str] = None,
        report_id: int = 0,
        crop_type: str = "Crop",
        decision: str = "reviewed",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Notify crop reporter via SMS and/or email on expert decision (e.g. rejection or approval).
        """
        note_str = f" Notes: {notes}" if notes else ""
        msg = f"CropHealth Alert: Your report #{report_id} ({crop_type}) status is now {decision.upper()}.{note_str}"
        sms_res = None
        email_res = None

        if user_phone:
            sms_res = self.send_sms(to_phone=user_phone, message=msg)
        if user_email:
            email_res = self.send_email(
                to_email=user_email,
                subject=f"CropHealth Report #{report_id} Update: {decision.capitalize()}",
                content=msg
            )

        return {
            "notified": bool(sms_res or email_res),
            "sms": sms_res,
            "email": email_res,
            "message": msg
        }

notification_service = NotificationService()
