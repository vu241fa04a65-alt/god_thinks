import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.models.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
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
        "email": "farmer1@example.com",
        "username": "farmer1",
        "password": "SecretPassword123",
        "phone_number": "+1234567890",
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
    assert me_res.json()["username"] == "farmer1"

    # 4. Create Farmer Report
    report_data = {
        "title": "Blight on lower tomato leaves",
        "crop_name": "Tomato",
        "description": "Spots spreading after monsoon rain.",
        "location_lat": 17.385,
        "location_lon": 78.4867
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
