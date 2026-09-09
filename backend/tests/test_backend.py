import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.models.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

def test_auth_workflow():
    # 1. Register farmer
    register_payload = {
        "name": "Farmer John",
        "email": "farmer1@example.com",
        "username": "farmer1",
        "password": "SecretPassword123",
        "role": "farmer"
    }
    r = client.post("/api/v1/auth/register", json=register_payload)
    assert r.status_code in [200, 400]  # 400 if already created in persistent test DB

    # 2. Login
    login_data = {
        "username": "farmer1",
        "password": "SecretPassword123"
    }
    login_res = client.post("/api/v1/auth/login", data=login_data)
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Read /me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["name"] == "Farmer John"

    # 4. Create Farmer Report
    report_data = {
        "crop_type": "Tomato",
        "image_url": "https://example.com/leaf.jpg",
        "location": "Hyderabad, Telangana"
    }
    report_res = client.post("/api/v1/reports/", json=report_data, headers=headers)
    assert report_res.status_code == 200
    report_id = report_res.json()["id"]

    # 5. Disease Detection with mock image
    img = Image.new("RGB", (100, 100), color="green")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    files = {"file": ("leaf.jpg", img_byte_arr, "image/jpeg")}
    detect_res = client.post("/api/v1/disease/detect", files=files, data={"target_lang": "en"}, headers=headers)
    assert detect_res.status_code == 200
    assert "disease_name" in detect_res.json()
    assert detect_res.json()["points_awarded"] == 20

    # 6. Gamification points summary
    points_res = client.get("/api/v1/gamification/summary", headers=headers)
    assert points_res.status_code == 200
    assert points_res.json()["total_points"] > 0

    # 7. Community feed
    feed_res = client.get("/api/v1/community/feed")
    assert feed_res.status_code == 200
    assert isinstance(feed_res.json(), list)

def test_rest_apis_suite():
    # 1. POST /auth/register and POST /auth/login (JSON)
    reg_res = client.post("/auth/register", json={
        "name": "Maria Garcia",
        "email": "maria@agri.io",
        "username": "maria_agri",
        "password": "Password123!",
        "role": "farmer"
    })
    assert reg_res.status_code == 200
    user_id = reg_res.json()["id"]

    login_res = client.post("/auth/login", json={
        "username": "maria_agri",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. POST /reports/upload (image upload + ML inference)
    img = Image.new("RGB", (128, 128), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    upload_res = client.post(
        "/reports/upload",
        files={"file": ("leaf_test.jpg", buf, "image/jpeg")},
        data={"crop_type": "Tomato", "location": "Andhra Pradesh Field B"},
        headers=headers
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    report_id = upload_data["report_id"]
    assert "disease_prediction" in upload_data
    assert "treatment_advisory" in upload_data
    assert upload_data["points_awarded"] == 20

    # 3. GET /reports/{id} (disease prediction + treatment advisory)
    report_res = client.get(f"/reports/{report_id}")
    assert report_res.status_code == 200
    report_detail = report_res.json()
    assert report_detail["report"]["id"] == report_id
    assert "disease_prediction" in report_detail
    assert "treatment_advisory" in report_detail
    assert "treatment" in report_detail["treatment_advisory"]

    # Test report not found error handling
    not_found = client.get("/reports/99999")
    assert not_found.status_code == 404

    # 4. GET /community/trends (aggregate outbreak data)
    trends_res = client.get("/community/trends")
    assert trends_res.status_code == 200
    trends_data = trends_res.json()
    assert trends_data["status"] == "success"
    assert "total_reported_cases" in trends_data
    assert "aggregate_trends" in trends_data
    assert len(trends_data["aggregate_trends"]) > 0

    # 5. POST /gamification/reward (add points)
    reward_res = client.post("/gamification/reward", json={
        "user_id": user_id,
        "points": 50,
        "reason": "Submitted high-accuracy diseased sample"
    }, headers=headers)
    assert reward_res.status_code == 200
    reward_data = reward_res.json()
    assert reward_data["status"] == "success"
    assert reward_data["points_added"] == 50

    # Test negative points error handling
    bad_reward = client.post("/gamification/reward", json={
        "user_id": user_id,
        "points": -10,
        "reason": "Invalid"
    }, headers=headers)
    assert bad_reward.status_code == 400

    # 6. POST /expert/validate (approve/reject prediction)
    val_res = client.post("/expert/validate", json={
        "report_id": report_id,
        "status": "approved",
        "expert_notes": "Confirmed by certified agronomist",
        "corrected_disease": "Tomato Early Blight"
    })
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["status"] == "success"
    assert val_data["validation_status"] == "verified"

    # Test invalid status error handling
    bad_val = client.post("/expert/validate", json={
        "report_id": report_id,
        "status": "invalid_status"
    })
    assert bad_val.status_code == 400

    # 7. GET /weather/risk (forecast pest/disease risk)
    weather_res = client.get("/weather/risk?lat=17.3850&lon=78.4867&crop_type=Tomato")
    assert weather_res.status_code == 200
    weather_data = weather_res.json()
    assert weather_data["status"] == "success"
    assert "risk_assessment" in weather_data
    assert "overall_risk_level" in weather_data["risk_assessment"]
    assert "ipm_recommendations" in weather_data["risk_assessment"]

    # Test out of bounds latitude error handling
    bad_lat = client.get("/weather/risk?lat=999&lon=78.4867")
    assert bad_lat.status_code == 422  # validation error from pydantic/fastapi

    # 8. POST /alerts/sms (send SMS notification)
    sms_res = client.post("/alerts/sms", json={
        "phone_number": "+919876543210",
        "message": "CropHealth Alert: Early blight outbreak warning in your sector."
    })
    assert sms_res.status_code == 200
    sms_data = sms_res.json()
    assert sms_data["status"] == "success"
    assert sms_data["recipient"] == "+919876543210"

    # Test empty message error handling
    bad_sms = client.post("/alerts/sms", json={
        "phone_number": "+919876543210",
        "message": ""
    })
    assert bad_sms.status_code == 400
