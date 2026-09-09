import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.weather_service import weather_service

client = TestClient(app)


def test_weather_service_compute_risk():
    """Test compute_risk logic with crop-specific rules from crop_rules.yaml."""
    location = {"lat": 17.3850, "lng": 78.4867}
    result = weather_service.compute_risk(
        crop_type="Tomato",
        location=location,
        forecast_days=3
    )

    assert "risk_score" in result
    assert isinstance(result["risk_score"], int)
    assert 0 <= result["risk_score"] <= 100

    assert "risk_reasons" in result
    assert isinstance(result["risk_reasons"], list)
    assert len(result["risk_reasons"]) > 0

    assert "recommended_preventive_actions" in result
    assert isinstance(result["recommended_preventive_actions"], list)
    assert len(result["recommended_preventive_actions"]) > 0

    assert result["crop_type"] == "Tomato"
    assert result["forecast_days"] == 3
    assert "weather_summary" in result


def test_weather_service_different_crops():
    """Test risk computation across different crops defined in crop_rules.yaml."""
    location = (20.5937, 78.9629)
    for crop in ["Potato", "Corn", "Apple", "Grape", "UnknownCrop"]:
        res = weather_service.compute_risk(crop_type=crop, location=location, forecast_days=2)
        assert 0 <= res["risk_score"] <= 100
        assert len(res["recommended_preventive_actions"]) > 0


def test_weather_risk_endpoint_query_params():
    """Test GET /weather/risk endpoint with lat, lng, and crop parameters."""
    response = client.get("/weather/risk?lat=18.5204&lng=73.8567&crop=Tomato&forecast_days=3")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "risk_score" in data
    assert "recommended_preventive_actions" in data
    assert isinstance(data["recommended_preventive_actions"], list)
    assert len(data["recommended_preventive_actions"]) > 0
    assert 0 <= data["risk_score"] <= 100


def test_weather_risk_endpoint_aliases():
    """Test GET /weather/risk with alias params (lon, crop_type)."""
    response = client.get("/weather/risk?lat=12.9716&lon=77.5946&crop_type=Potato")
    assert response.status_code == 200
    data = response.json()
    assert data["crop_type"] == "Potato"
    assert "risk_score" in data
    assert "recommended_preventive_actions" in data
