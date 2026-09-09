import requests
from backend.app.config import settings
from backend.app.utils.logger import logger

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY

    def get_forecast(self, lat: float, lon: float) -> dict:
        if self.api_key:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "temperature_c": data["main"]["temp"],
                        "humidity_percent": data["main"]["humidity"],
                        "condition": data["weather"][0]["description"].title(),
                        "wind_speed_kmh": data["wind"]["speed"] * 3.6,
                        "advisory": "Favorable conditions for field scouting."
                    }
            except Exception as e:
                logger.warning(f"Weather API request failed: {e}. Using fallback forecast.")

        # Fallback advisory
        return {
            "temperature_c": 27.5,
            "humidity_percent": 68,
            "condition": "Partly Cloudy",
            "wind_speed_kmh": 12.0,
            "advisory": "High morning humidity detected. Monitor fields for fungal spores."
        }

weather_service = WeatherService()
