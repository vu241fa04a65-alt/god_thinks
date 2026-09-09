import os
from typing import Union, Dict, Any, List, Tuple, Optional
import requests
import yaml

from backend.app.config import settings
from backend.app.utils.logger import logger

RULES_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config", "crop_rules.yaml")
)


class WeatherService:
    """
    Microservice for weather retrieval and crop-specific microclimate risk assessment.
    Integrates with OpenWeatherMap API and evaluates multi-day risk rules from crop_rules.yaml.
    """
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.rules = self._load_crop_rules()

    def _load_crop_rules(self) -> Dict[str, Any]:
        """Load crop vulnerability rules from YAML configuration file."""
        if os.path.exists(RULES_FILE_PATH):
            try:
                with open(RULES_FILE_PATH, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        logger.info(f"Loaded crop rules for {len(data)} crops from {RULES_FILE_PATH}")
                        return data
            except Exception as e:
                logger.error(f"Error loading crop rules YAML ({RULES_FILE_PATH}): {e}")

        # In-memory fallback rules if YAML is missing
        return {
            "Default": {
                "fungal": {"min_humidity": 70, "min_temp": 16.0, "max_temp": 28.0, "rain_probability_threshold": 40, "risk_weight": 40, "diseases": ["Foliar Blight"]},
                "bacterial": {"min_humidity": 75, "min_temp": 24.0, "max_temp": 32.0, "rain_probability_threshold": 50, "risk_weight": 30, "diseases": ["Bacterial Spot"]},
                "pest": {"max_humidity": 55, "min_temp": 28.0, "risk_weight": 30, "pests": ["Aphids/Mites"]},
                "preventive_actions": ["Maintain regular crop scouting and field drainage."]
            }
        }

    def _get_crop_rule(self, crop_type: str) -> Dict[str, Any]:
        """Lookup crop rules with case-insensitive match, defaulting to 'Default'."""
        crop_clean = crop_type.strip().lower()
        for key, val in self.rules.items():
            if key.lower() == crop_clean:
                return val
        # Check partial containment (e.g. "tomato early blight" -> Tomato)
        for key, val in self.rules.items():
            if key.lower() in crop_clean:
                return val
        return self.rules.get("Default", {})

    def _parse_location(self, location: Union[Dict[str, Any], Tuple[float, float], str]) -> Tuple[float, float, str]:
        """Standardize location input into (lat, lon, label)."""
        lat, lon = 17.3850, 78.4867
        label = "Hyderabad Agricultural Sector"

        if isinstance(location, dict):
            lat = float(location.get("lat", location.get("latitude", 17.3850)))
            lon = float(location.get("lng", location.get("lon", location.get("longitude", 78.4867))))
            label = str(location.get("name", f"Coordinates ({lat:.4f}, {lon:.4f})"))
        elif isinstance(location, (list, tuple)) and len(location) >= 2:
            lat, lon = float(location[0]), float(location[1])
            label = f"Coordinates ({lat:.4f}, {lon:.4f})"
        elif isinstance(location, str):
            if "," in location:
                parts = location.split(",")
                try:
                    lat, lon = float(parts[0].strip()), float(parts[1].strip())
                    label = f"Coordinates ({lat:.4f}, {lon:.4f})"
                except ValueError:
                    label = location
            else:
                label = location

        return lat, lon, label

    def get_forecast(self, lat: float, lon: float, days: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch forecast from OpenWeatherMap 5-day forecast API, or generate realistic fallback periods.
        """
        periods: List[Dict[str, Any]] = []

        if self.api_key:
            try:
                url = (
                    f"https://api.openweathermap.org/data/2.5/forecast"
                    f"?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
                )
                res = requests.get(url, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    # Each forecast item represents 3 hours (8 entries = 1 day)
                    max_entries = min(len(data.get("list", [])), days * 8)
                    for item in data.get("list", [])[:max_entries]:
                        periods.append({
                            "dt_txt": item.get("dt_txt"),
                            "temperature_c": item.get("main", {}).get("temp", 26.0),
                            "humidity_percent": item.get("main", {}).get("humidity", 65),
                            "rain_probability": int(item.get("pop", 0.0) * 100),
                            "condition": item.get("weather", [{}])[0].get("description", "Clear").title(),
                            "wind_speed_kmh": item.get("wind", {}).get("speed", 3.0) * 3.6
                        })
                    if periods:
                        return periods
            except Exception as e:
                logger.warning(f"OpenWeatherMap forecast request failed ({e}). Using deterministic forecast simulation.")

        # Deterministic multi-day simulation when offline or API key missing
        for d in range(1, days + 1):
            for slot, (hour, temp_offset, hum_offset, rain_p) in enumerate([
                ("06:00:00", -4.0, 18, 45),
                ("12:00:00", 3.5, -12, 20),
                ("18:00:00", 0.0, 5, 30),
                ("21:00:00", -2.5, 12, 40)
            ]):
                periods.append({
                    "dt_txt": f"Day +{d} {hour}",
                    "temperature_c": round(25.0 + temp_offset + (d * 0.5), 1),
                    "humidity_percent": min(95, max(40, 72 + hum_offset)),
                    "rain_probability": min(100, rain_p + (d * 5)),
                    "condition": "Scattered Clouds" if rain_p < 40 else "Light Rain Shower",
                    "wind_speed_kmh": round(11.0 + (d * 1.5), 1)
                })

        return periods

    def compute_risk(
        self,
        crop_type: str,
        location: Union[Dict[str, Any], Tuple[float, float], str],
        forecast_days: int = 3
    ) -> Dict[str, Any]:
        """
        Compute disease and pest risk score (0-100) and risk reasons based on
        weather variables and crop-specific susceptibility rules from crop_rules.yaml.
        """
        lat, lon, loc_name = self._parse_location(location)
        periods = self.get_forecast(lat=lat, lon=lon, days=forecast_days)
        crop_rule = self._get_crop_rule(crop_type)

        if not periods:
            return {
                "risk_score": 25,
                "risk_reasons": ["Baseline seasonal risk (weather data temporarily unavailable)"],
                "risk_level": "Low",
                "recommended_preventive_actions": crop_rule.get("preventive_actions", [])
            }

        # Aggregate weather variables over the forecast window
        temps = [p["temperature_c"] for p in periods]
        humidities = [p["humidity_percent"] for p in periods]
        rain_probs = [p["rain_probability"] for p in periods]

        avg_temp = sum(temps) / len(temps)
        avg_hum = sum(humidities) / len(humidities)
        max_hum = max(humidities)
        max_rain_p = max(rain_probs)

        # Evaluate risk components
        score = 15.0  # Base natural vulnerability
        reasons: List[str] = []

        fungal_rule = crop_rule.get("fungal", {})
        bacterial_rule = crop_rule.get("bacterial", {})
        pest_rule = crop_rule.get("pest", {})

        # 1. Fungal Pathogen Vulnerability
        f_hum = fungal_rule.get("min_humidity", 70)
        f_min_t = fungal_rule.get("min_temp", 16.0)
        f_max_t = fungal_rule.get("max_temp", 28.0)
        f_rain_th = fungal_rule.get("rain_probability_threshold", 40)
        f_weight = fungal_rule.get("risk_weight", 40)

        fungal_triggered = False
        if max_hum >= f_hum and (f_min_t <= avg_temp <= f_max_t):
            fungal_triggered = True
            hum_severity = min(1.0, (max_hum - f_hum + 10) / 30.0)
            score += f_weight * hum_severity
            diseases_str = ", ".join(fungal_rule.get("diseases", ["Foliar Blight"])[:2])
            reasons.append(
                f"Peak atmospheric humidity of {max_hum}% within optimal fungal germination window "
                f"({f_min_t}°C - {f_max_t}°C) significantly heightens risk of {diseases_str}."
            )

        if max_rain_p >= f_rain_th:
            score += 15.0
            reasons.append(
                f"Elevated precipitation probability of {max_rain_p}% prolongs canopy leaf wetness and soil splashing."
            )

        # 2. Bacterial Pathogen Vulnerability
        b_hum = bacterial_rule.get("min_humidity", 75)
        b_min_t = bacterial_rule.get("min_temp", 22.0)
        b_max_t = bacterial_rule.get("max_temp", 32.0)
        b_weight = bacterial_rule.get("risk_weight", 30)

        if avg_hum >= b_hum and (b_min_t <= avg_temp <= b_max_t):
            score += b_weight * 0.75
            b_diseases_str = ", ".join(bacterial_rule.get("diseases", ["Bacterial Spot"])[:2])
            reasons.append(
                f"Warm, saturated ambient conditions (avg {round(avg_temp, 1)}°C, {round(avg_hum, 1)}% humidity) "
                f"favor bacterial colonization of {b_diseases_str}."
            )

        # 3. Pest Proliferation Vulnerability
        p_max_hum = pest_rule.get("max_humidity", 55)
        p_min_t = pest_rule.get("min_temp", 26.0)
        p_weight = pest_rule.get("risk_weight", 25)

        if avg_hum <= p_max_hum and avg_temp >= p_min_t:
            score += p_weight
            pests_str = ", ".join(pest_rule.get("pests", ["Aphids/Mites"])[:2])
            reasons.append(
                f"Dry, warm atmospheric conditions (avg {round(avg_temp, 1)}°C, {round(avg_hum, 1)}% humidity) "
                f"accelerate pest reproduction cycles ({pests_str})."
            )

        # Final score bounding
        final_score = int(round(min(100.0, max(0.0, score))))
        risk_level = "High" if final_score >= 65 else ("Moderate" if final_score >= 40 else "Low")

        if not reasons:
            reasons.append("Mild atmospheric conditions observed with no acute microclimate threat triggers.")

        preventive_actions = crop_rule.get("preventive_actions", [
            "Maintain standard weekly scouting and clean field drainage."
        ])

        return {
            "risk_score": final_score,
            "risk_reasons": reasons,
            "risk_level": risk_level,
            "crop_type": crop_type,
            "location": {
                "lat": lat,
                "lon": lon,
                "label": loc_name
            },
            "forecast_days": forecast_days,
            "weather_summary": {
                "avg_temp_c": round(avg_temp, 1),
                "avg_humidity_percent": round(avg_hum, 1),
                "peak_humidity_percent": max_hum,
                "max_rain_probability": max_rain_p
            },
            "recommended_preventive_actions": preventive_actions
        }

    # Backward compatibility helper
    def compute_risk_score(self, forecast: dict, crop_type: str = "Tomato") -> dict:
        result = self.compute_risk(crop_type=crop_type, location={"lat": 17.385, "lon": 78.4867}, forecast_days=3)
        return {
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "crop_evaluated": crop_type,
            "primary_threats": result["risk_reasons"],
            "recommendation": result["recommended_preventive_actions"][0] if result["recommended_preventive_actions"] else "Standard scouting"
        }


weather_service = WeatherService()
