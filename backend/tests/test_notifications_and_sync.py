import io
import time
import base64
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.database import Base, engine, SessionLocal
from backend.app.models.entities import User, Report, DiseasePrediction, CommunityTrend, Reward
from backend.app.services.notification_service import notification_service, NotificationService

client = TestClient(app)


def create_test_base64_image() -> str:
    img = Image.new("RGB", (32, 32), color=(255, 140, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@pytest.fixture(autouse=True)
def setup_db():
    notification_service.clear_throttle()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # User 1: Opted-IN in Hyderabad
        u1 = User(
            id=1,
            name="Suresh Reddy",
            email="suresh@example.com",
            phone="+919111111111",
            username="suresh_r",
            sms_opt_in=True,
            location="Hyderabad East",
            location_lat=17.3850,
            location_lng=78.4867,
            points=0
        )
        # User 2: Opted-OUT in Hyderabad
        u2 = User(
            id=2,
            name="Anil Verma",
            email="anil@example.com",
            phone="+919222222222",
            username="anil_v",
            sms_opt_in=False,
            location="Hyderabad West",
            location_lat=17.3900,
            location_lng=78.4900,
            points=0
        )
        # User 3: Opted-IN in Ludhiana (~1500 km away from Hyderabad)
        u3 = User(
            id=3,
            name="Gurpreet Singh",
            email="gurpreet@example.com",
            phone="+919333333333",
            username="gurpreet_s",
            sms_opt_in=True,
            location="Ludhiana",
            location_lat=30.9010,
            location_lng=75.8573,
            points=0
        )
        db.add_all([u1, u2, u3])
        db.commit()

    yield
    notification_service.clear_throttle()


def test_notification_service_send_and_throttling():
    svc = NotificationService(throttle_seconds=2)
    phone = "+919998887776"
    msg = "Test message for dispatch"

    # 1. First send: success
    res1 = svc.send_sms(to_phone=phone, message=msg)
    assert res1["status"] == "sent"
    assert res1["recipient"] == phone

    # 2. Immediate second send: throttled to avoid spam
    res2 = svc.send_sms(to_phone=phone, message=msg)
    assert res2["status"] == "throttled"
    assert "rate limit" in res2["reason"]

    # 3. Bypass throttle flag: allowed
    res3 = svc.send_sms(to_phone=phone, message=msg, bypass_throttle=True)
    assert res3["status"] == "sent"


def test_notification_service_queue_async_dispatch():
    svc = NotificationService(throttle_seconds=0)
    recipients = ["+919000000001", "+919000000002", "+919000000003"]
    msg = "Urgent: Locust swarm sighted in neighboring sector."

    queue_res = svc.queue_sms(message=msg, recipients=recipients, bypass_throttle=True)
    assert queue_res["status"] == "enqueued"
    assert queue_res["queued_count"] == 3

    # Drain queue
    results = svc.drain_queue()
    assert len(results) == 3
    assert all(r["status"] == "sent" for r in results)


def test_alerts_sms_direct_respects_opt_in():
    # User 1 has opted in
    res_opt_in = client.post("/alerts/sms", json={
        "phone_number": "+919111111111",
        "message": "Field Alert: Powdery mildew detected."
    })
    assert res_opt_in.status_code == 200
    assert res_opt_in.json()["status"] == "success"

    # User 2 has opted out of SMS
    res_opt_out = client.post("/alerts/sms", json={
        "phone_number": "+919222222222",
        "message": "Field Alert: Powdery mildew detected."
    })
    assert res_opt_out.status_code == 200
    assert res_opt_out.json()["status"] == "skipped"
    assert res_opt_out.json()["sms_opt_in"] is False


def test_alerts_sms_geofence_outbreak_broadcast():
    # Trigger alert for Hyderabad region: lat=17.3850, lng=78.4867, radius=30 km
    # User 1 is in Hyderabad and opted-in -> should receive
    # User 2 is in Hyderabad but opted-out -> should NOT receive
    # User 3 is in Ludhiana (outside 30 km) -> should NOT receive
    payload = {
        "message": "URGENT OUTBREAK: Late Blight reported in Hyderabad sector. Apply fungicide immediately.",
        "lat": 17.3850,
        "lng": 78.4867,
        "radius_km": 30.0
    }
    res = client.post("/alerts/sms", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["matched_users_count"] == 1
    assert "+919111111111" in data["queued_recipients"]
    assert "+919222222222" not in data["queued_recipients"]  # opted out
    assert "+919333333333" not in data["queued_recipients"]  # outside geo-fence


def test_alerts_sms_validation():
    # Empty message
    bad_msg = client.post("/alerts/sms", json={"phone_number": "+919876543210", "message": ""})
    assert bad_msg.status_code == 400

    # Missing phone and missing geo-fence
    missing_dest = client.post("/alerts/sms", json={"message": "Hello world"})
    assert missing_dest.status_code == 400


def test_alerts_opt_in_preference_toggle():
    # Toggle user 2 back to opted in
    res = client.post("/alerts/opt-in?user_id=2&opt_in=true")
    assert res.status_code == 200
    assert res.json()["data"]["sms_opt_in"] is True

    # Now direct SMS should succeed
    sms_res = client.post("/alerts/sms", json={
        "phone_number": "+919222222222",
        "message": "Welcome back to crop alerts"
    })
    assert sms_res.json()["status"] == "success"


def test_offline_sync_batch_processing():
    img_b64 = create_test_base64_image()
    batch_payload = {
        "client_id": "mobile_device_xyz",
        "device_id": "android_offline_v1",
        "reports": [
            {
                "offline_id": "offline_uuid_001",
                "crop": "Tomato",
                "symptoms": "Dark brown early blight lesions on leaf margins",
                "location": "Remote Village Sector 4",
                "lat": 17.4000,
                "lng": 78.5000,
                "image_base64": img_b64,
                "captured_at": "2026-09-09T10:00:00Z",
                "user_id": 1
            },
            {
                "offline_id": "offline_uuid_002",
                "crop": "Wheat",
                "symptoms": "Yellow rust pustules in linear rows",
                "location": "Punjab Border Field",
                "lat": 31.2000,
                "lng": 75.4000,
                "captured_at": "2026-09-09T11:30:00Z",
                "user_id": 1
            }
        ]
    }

    res = client.post("/sync/batch", json=batch_payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_received"] == 2
    assert data["synced_count"] == 2
    assert data["points_awarded_total"] == 2  # 1 point each
    synced = data["synced_reports"]
    assert len(synced) == 2

    # Check ID mapping
    assert synced[0]["offline_id"] == "offline_uuid_001"
    assert synced[0]["status"] == "synced"
    assert synced[0]["server_report_id"] is not None
    assert synced[0]["image_url"] is not None

    assert synced[1]["offline_id"] == "offline_uuid_002"
    assert synced[1]["status"] == "synced"

    # Verify Database persistence
    with SessionLocal() as db:
        reports = db.query(Report).all()
        assert len(reports) >= 2

        # Verify predictions were created
        preds = db.query(DiseasePrediction).all()
        assert len(preds) >= 2

        # Verify user 1 points incremented
        user1 = db.query(User).filter(User.id == 1).first()
        assert user1.points == 2
