from backend.app.config import settings
from backend.app.utils.logger import logger

class SMSService:
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        self.client = None

        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio SMS Client initialized.")
            except Exception as e:
                logger.warning(f"Could not initialize Twilio client: {e}")

    def send_alert(self, to_phone: str, message: str) -> dict:
        if self.client and self.from_phone:
            try:
                msg = self.client.messages.create(
                    body=message,
                    from_=self.from_phone,
                    to=to_phone
                )
                logger.info(f"SMS alert sent via Twilio to {to_phone}, SID: {msg.sid}")
                return {"status": "sent", "sid": msg.sid}
            except Exception as e:
                logger.error(f"Failed to send SMS via Twilio: {e}")

        # Fallback simulation
        logger.info(f"[SIMULATED SMS ALERT] To: {to_phone} | Body: {message}")
        return {"status": "simulated", "message": message, "to": to_phone}

sms_service = SMSService()
