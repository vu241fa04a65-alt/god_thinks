from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["Weather & Microclimate"])

@router.get("/risk")
def get_weather_risk(
    lat: float = Query(17.3850, ge=-90.0, le=90.0, description="Latitude"),
    lon: float = Query(78.4867, ge=-180.0, le=180.0, description="Longitude"),
    crop_type: Optional[str] = Query("Tomato", description="Crop type to assess")
):
    try:
        forecast = weather_service.get_forecast(lat=lat, lon=lon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather forecast: {str(e)}")

    temp = forecast.get("temperature_c", 25.0)
    humidity = forecast.get("humidity_percent", 60)
    wind_speed = forecast.get("wind_speed_kmh", 10.0)

    # Pest and Disease Risk Modeling
    fungal_risk = "Low"
    pest_risk = "Low"
    threats = []
    actions = []

    if humidity >= 70:
        fungal_risk = "High"
        threats.append("Late Blight & Downy Mildew spore germination")
        actions.append("Avoid overhead irrigation; schedule preventive bio-fungicide within 24 hours.")
    elif humidity >= 50:
        fungal_risk = "Moderate"
        threats.append("Early Blight foliar lesion development")
        actions.append("Ensure crop canopy ventilation and prune touching bottom leaves.")

    if temp >= 30 and humidity < 60:
        pest_risk = "High"
        threats.append("Spider mites & Whitefly colony surge")
        actions.append("Deploy yellow sticky traps and inspect leaf undersides.")
    elif temp >= 24:
        pest_risk = "Moderate"
        threats.append("Aphid & Thrips activity")
        actions.append("Monitor field boundaries for weed-borne insect vectors.")

    overall_risk = "High" if ("High" in [fungal_risk, pest_risk]) else ("Moderate" if ("Moderate" in [fungal_risk, pest_risk]) else "Low")

    if not actions:
        actions.append("Conditions optimal for field cultivation. Maintain standard weekly scouting.")

    return {
        "status": "success",
        "location": {
            "lat": lat,
            "lon": lon
        },
        "crop_type": crop_type,
        "weather_conditions": forecast,
        "risk_assessment": {
            "overall_risk_level": overall_risk,
            "fungal_infection_risk": fungal_risk,
            "pest_outbreak_risk": pest_risk,
            "primary_threats": threats,
            "ipm_recommendations": actions
        }
    }
