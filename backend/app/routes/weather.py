from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from backend.app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["Weather Risk"])


@router.get("/risk")
def get_weather_risk(
    lat: float = Query(17.3850, ge=-90.0, le=90.0, description="Latitude"),
    lng: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude alias"),
    crop: Optional[str] = Query(None, description="Crop name"),
    crop_type: Optional[str] = Query(None, description="Crop type alias"),
    forecast_days: int = Query(3, ge=1, le=7, description="Forecast projection in days")
):
    """
    Evaluate microclimate pest and disease risk score (0-100) and recommended preventive actions
    based on multi-day forecast and crop-specific rules from crop_rules.yaml.
    """
    longitude = lng if lng is not None else (lon if lon is not None else 78.4867)
    selected_crop = crop or crop_type or "Tomato"

    try:
        risk_result = weather_service.compute_risk(
            crop_type=selected_crop,
            location={"lat": lat, "lng": longitude},
            forecast_days=forecast_days
        )

        return {
            "status": "success",
            "success": True,
            "crop_type": selected_crop,
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "risk_reasons": risk_result["risk_reasons"],
            "recommended_preventive_actions": risk_result["recommended_preventive_actions"],
            "location": risk_result["location"],
            "forecast_days": risk_result["forecast_days"],
            "weather_conditions": risk_result["weather_summary"],
            "weather_summary": risk_result["weather_summary"],
            "risk_assessment": {
                "overall_risk_level": risk_result["risk_level"],
                "risk_score": risk_result["risk_score"],
                "primary_threats": risk_result["risk_reasons"],
                "ipm_recommendations": risk_result["recommended_preventive_actions"]
            },
            "data": risk_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate weather risk: {str(e)}")
