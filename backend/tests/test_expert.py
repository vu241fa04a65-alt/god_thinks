import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.database import Base, engine, SessionLocal
from backend.app.models.entities import (
    User,
    Report,
    DiseasePrediction,
    CommunityTrend,
    ExpertAction,
    Reward
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # Create reporter farmer
        farmer = User(
            id=1,
            name="Kisan Ramesh",
            email="ramesh.farmer@example.com",
            phone="+919876543210",
            username="ramesh_k",
            role="farmer",
            points=10
        )
        # Create expert agronomist
        expert = User(
            id=2,
            name="Dr. Radhika Rao",
            email="radhika.expert@example.com",
            phone="+919876543211",
            username="dr_radhika",
            role="expert",
            points=100
        )
        db.add_all([farmer, expert])
        db.flush()

        # Create pending reports
        r1 = Report(
            id=101,
            user_id=farmer.id,
            crop_type="Tomato",
            location="Guntur North Village",
            location_lat=16.3067,
            location_lng=80.4365,
            image_path="/storage/uploads/tomato_leaf_101.jpg",
            status="pending",
            notes="Brown concentric rings on lower leaves"
        )
        r2 = Report(
            id=102,
            user_id=farmer.id,
            crop_type="Wheat",
            location="Ludhiana Sector 2",
            location_lat=30.9010,
            location_lng=75.8573,
            image_path="/storage/uploads/wheat_leaf_102.jpg",
            status="pending",
            notes="Yellowish powdery spots"
        )
        db.add_all([r1, r2])
        db.flush()

        # Create disease predictions with overlays
        pred1 = DiseasePrediction(
            id=201,
            report_id=r1.id,
            disease_name="Tomato Early Blight",
            confidence=0.94,
            overlay_path="/storage/overlays/overlay_101.png",
            explanation_text="Grad-CAM highlights concentric necrotic lesions on target leaf lamina"
        )
        pred2 = DiseasePrediction(
            id=202,
            report_id=r2.id,
            disease_name="Wheat Stripe Rust",
            confidence=0.88,
            overlay_path="/storage/overlays/overlay_102.png",
            explanation_text="Heatmap clusters around linear yellow pustule formations"
        )
        db.add_all([pred1, pred2])
        db.commit()

    yield


def test_get_expert_pending_list():
    res = client.get("/expert/pending")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 2
    reports = data["pending_reports"]
    assert len(reports) == 2

    r1 = next(r for r in reports if r["report_id"] == 101)
    assert r1["crop_type"] == "Tomato"
    assert r1["status"] == "pending"
    assert r1["reporter"]["name"] == "Kisan Ramesh"
    assert len(r1["predictions"]) == 1
    assert r1["predictions"][0]["disease_name"] == "Tomato Early Blight"
    assert "overlay_url" in r1["predictions"][0]

    # Test filtering by crop
    res_crop = client.get("/expert/pending?crop_type=Wheat")
    assert res_crop.status_code == 200
    wheat_data = res_crop.json()["data"]
    assert wheat_data["total"] == 1
    assert wheat_data["pending_reports"][0]["crop_type"] == "Wheat"


def test_expert_validate_approval_workflow():
    payload = {
        "report_id": 101,
        "decision": "approve",
        "notes": "Verified severe Early Blight. Prescribe copper hydroxide treatment.",
        "corrected_disease": "Tomato Early Blight"
    }
    res = client.post("/expert/validate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["decision"] == "approved"
    assert data["status"] == "validated"
    assert data["points_awarded"] == 5
    assert data["community_trend_updated"] is True
    assert "action_id" in data

    # Verify DB changes
    with SessionLocal() as db:
        # 1. Report status updated to validated
        report = db.query(Report).filter(Report.id == 101).first()
        assert report.status == "validated"
        assert "Verified severe Early Blight" in report.notes

        # 2. Farmer points awarded (+5 points)
        farmer = db.query(User).filter(User.id == 1).first()
        assert farmer.points == 15  # started with 10 + 5

        # 3. Community trend updated/incremented
        trend = db.query(CommunityTrend).filter(
            CommunityTrend.disease_name.ilike("Tomato Early Blight")
        ).first()
        assert trend is not None
        assert trend.count >= 1

        # 4. Audit trail recorded in expert_actions
        action = db.query(ExpertAction).filter(ExpertAction.report_id == 101).first()
        assert action is not None
        assert action.decision == "approved"
        assert "copper hydroxide" in action.notes


def test_expert_validate_rejection_workflow():
    payload = {
        "report_id": 102,
        "decision": "reject",
        "notes": "Image blurry and symptoms indicate minor nutrient deficiency, not Stripe Rust."
    }
    res = client.post("/expert/validate", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["decision"] == "rejected"
    assert data["status"] == "rejected"
    assert data["points_awarded"] == 0
    assert data["notification"] is not None
    assert data["notification"]["notified"] is True

    # Verify DB changes
    with SessionLocal() as db:
        # 1. Report status updated to rejected
        report = db.query(Report).filter(Report.id == 102).first()
        assert report.status == "rejected"
        assert "Expert Rejection" in report.notes

        # 2. Farmer points unchanged
        farmer = db.query(User).filter(User.id == 1).first()
        assert farmer.points == 10

        # 3. Audit trail recorded
        action = db.query(ExpertAction).filter(ExpertAction.report_id == 102).first()
        assert action is not None
        assert action.decision == "rejected"
        assert "nutrient deficiency" in action.notes


def test_expert_audit_trail_endpoint():
    # Perform an approval and a rejection
    client.post("/expert/validate", json={"report_id": 101, "decision": "approve", "notes": "Looks good"})
    client.post("/expert/validate", json={"report_id": 102, "decision": "reject", "notes": "Insufficient resolution"})

    res = client.get("/expert/actions")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 2
    actions = data["audit_actions"]
    decisions = [a["decision"] for a in actions]
    assert "approved" in decisions
    assert "rejected" in decisions


def test_expert_validate_invalid_inputs():
    # Invalid decision
    bad_decision = client.post("/expert/validate", json={
        "report_id": 101,
        "decision": "uncertain"
    })
    assert bad_decision.status_code == 400

    # Non-existent report
    not_found = client.post("/expert/validate", json={
        "report_id": 99999,
        "decision": "approve"
    })
    assert not_found.status_code == 404
