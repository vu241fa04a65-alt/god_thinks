# Re-export weather router from routes.weather for backward compatibility
from backend.app.routes.weather import router, get_weather_risk

__all__ = ["router", "get_weather_risk"]
