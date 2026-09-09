# Backward compatibility re-export
from backend.app.routes.alerts import router, send_sms_alert

__all__ = ["router", "send_sms_alert"]
