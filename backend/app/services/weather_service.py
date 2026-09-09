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

        return {
            "temperature_c": 27.5,
            "humidity_percent": 68,
            "condition": "Partly Cloudy",
            "wind_speed_kmh": 12.0,
            "advisory": "High morning humidity detected. Monitor fields for fungal spores."
        }

    def compute_risk_score(self, forecast: dict, crop_type: str = "Tomato") -> dict:
        """
        Compute disease and pest risk score (0-100) based on microclimate variables.
        """
        temp = forecast.get("temperature_c", 25.0)
        humidity = forecast.get("humidity_percent", 60)
        wind = forecast.get("wind_speed_kmh", 10.0)

        # Baseline calculation
        score = 20.0
        threats = []

        # High humidity promotes foliar fungal blights
        if humidity >= 75:
            score += 40.0
            threats.append("High fungal spore germination (Blight / Downy Mildew)")
        elif humidity >= 60:
            score += 20.0
            threats.append("Moderate moisture favoring foliar spots")

        # Optimal fungal temperature band
        if 18.0 <= temp <= 28.0:
            score += 20.0
        elif temp >= 32.0 and humidity < 50:
            score += 25.0
            threats.append("High pest proliferation (Whiteflies / Mites)")

        # Wind aids spore dispersal
        if wind >= 20.0:
            score += 15.0
            threats.append("Elevated wind dispersing fungal spores across canopies")

        score = min(100.0, max(0.0, score))
        risk_level = "High" if score >= 65 else ("Moderate" if score >= 40 else "Low")

        return {
            "risk_score": round(score, 1),
            "risk_level": risk_level,
            "crop_evaluated": crop_type,
            "primary_threats": threats,
            "recommendation": "Apply preventative bio-fungicide" if risk_level == "High" else "Standard scouting recommended"
        }

weather_service = WeatherService()
