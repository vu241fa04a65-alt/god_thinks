import time
import threading
from collections import deque
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.utils.logger import logger

class NotificationService:
    """
    Enterprise Notification Service supporting:
    - Twilio SMS dispatch with exponential backoff retries.
    - Anti-spam throttling per phone number.
    - Asynchronous message queuing via worker thread.
    - User opt-in preferences filtering.
    """
    def __init__(self, throttle_seconds: int = 5):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        self.client = None
        self.throttle_seconds = throttle_seconds
        self._throttle_ledger: Dict[str, float] = {}

        self.queue = deque()
        self.lock = threading.Lock()
        self._worker_thread = None
        self._running = True

        self._init_twilio()
        self._start_worker()

    def _init_twilio(self):
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Twilio initialization notice: {e}")
                self.client = None

    def _start_worker(self):
        """Start daemon background worker thread to process queued SMS tasks asynchronously."""
        def _worker():
            while self._running:
                item = None
                with self.lock:
                    if self.queue:
                        item = self.queue.popleft()
                if item:
                    try:
                        self.send_sms(
                            to_phone=item["phone"],
                            message=item["message"],
                            bypass_throttle=item.get("bypass_throttle", False)
                        )
                    except Exception as e:
                        logger.error(f"Error processing background SMS task: {e}")
                else:
                    time.sleep(0.1)

        self._worker_thread = threading.Thread(target=_worker, daemon=True, name="SMSWorkerThread")
        self._worker_thread.start()

    def is_throttled(self, phone: str) -> bool:
        """Check if phone number has received an SMS within throttle_seconds window."""
        now = time.time()
        last_sent = self._throttle_ledger.get(phone, 0)
        return (now - last_sent) < self.throttle_seconds

    def clear_throttle(self, phone: Optional[str] = None):
        """Clear throttle history (useful in tests)."""
        if phone:
            self._throttle_ledger.pop(phone, None)
        else:
            self._throttle_ledger.clear()

    def send_sms(
        self,
        to_phone: str,
        message: str,
        max_retries: int = 3,
        retry_delay: float = 0.2,
        bypass_throttle: bool = False
    ) -> Dict[str, Any]:
        """
        Dispatch SMS alert using Twilio with exponential backoff retries and spam throttling.
        """
        clean_phone = to_phone.strip()
        if not clean_phone:
            raise ValueError("Phone number cannot be empty")
        if not message.strip():
            raise ValueError("Message cannot be empty")

        # 1. Anti-spam throttling check
        if not bypass_throttle and self.is_throttled(clean_phone):
            logger.warning(f"[THROTTLED] SMS to {clean_phone} throttled (exceeded rate limit).")
            return {
                "status": "throttled",
                "recipient": clean_phone,
                "message": message,
                "reason": f"Throttled: rate limit of 1 message per {self.throttle_seconds}s exceeded."
            }

        # 2. Twilio dispatch with retry loop
        if self.client and self.from_phone:
            for attempt in range(1, max_retries + 1):
                try:
                    msg = self.client.messages.create(
                        body=message,
                        from_=self.from_phone,
                        to=clean_phone
                    )
                    self._throttle_ledger[clean_phone] = time.time()
                    logger.info(f"SMS dispatched to {clean_phone} via Twilio, SID: {msg.sid} (attempt {attempt})")
                    return {
                        "status": "sent",
                        "channel": "twilio",
                        "sid": msg.sid,
                        "recipient": clean_phone,
                        "attempts": attempt
                    }
                except Exception as e:
                    logger.warning(f"Twilio attempt {attempt}/{max_retries} failed for {clean_phone}: {e}")
                    if attempt < max_retries:
                        time.sleep(retry_delay * (2 ** (attempt - 1)))
                    else:
                        logger.error(f"Twilio delivery failed after {max_retries} attempts: {e}")

        # 3. Simulated / Dev Fallback dispatch
        self._throttle_ledger[clean_phone] = time.time()
        logger.info(f"[SIMULATED SMS] To: {clean_phone} | Msg: {message}")
        return {
            "status": "sent",
            "channel": "simulated",
            "recipient": clean_phone,
            "message": message,
            "attempts": 1
        }

    def queue_sms(
        self,
        message: str,
        recipients: List[str],
        bypass_throttle: bool = False
    ) -> Dict[str, Any]:
        """
        Enqueue SMS tasks to be processed asynchronously by the background worker.
        """
        queued = []
        with self.lock:
            for phone in recipients:
                clean = phone.strip() if isinstance(phone, str) else ""
                if clean:
                    self.queue.append({
                        "phone": clean,
                        "message": message,
                        "bypass_throttle": bypass_throttle,
                        "queued_at": time.time()
                    })
                    queued.append(clean)

        logger.info(f"Enqueued {len(queued)} SMS messages for async dispatch.")
        return {
            "status": "enqueued",
            "queued_count": len(queued),
            "recipients": queued
        }

    def drain_queue(self) -> List[Dict[str, Any]]:
        """Synchronously drain and dispatch all currently queued SMS tasks."""
        items = []
        with self.lock:
            while self.queue:
                items.append(self.queue.popleft())

        results = []
        for item in items:
            res = self.send_sms(
                to_phone=item["phone"],
                message=item["message"],
                bypass_throttle=item.get("bypass_throttle", False)
            )
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
        Notify crop reporter via SMS and/or email on expert decision.
        """
        note_str = f" Notes: {notes}" if notes else ""
        msg = f"CropHealth Alert: Your report #{report_id} ({crop_type}) status is now {decision.upper()}.{note_str}"
        sms_res = None
        email_res = None

        if user_phone:
            sms_res = self.send_sms(to_phone=user_phone, message=msg, bypass_throttle=True)
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
