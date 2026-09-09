import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.database import Base, engine, SessionLocal
from backend.app.models.entities import User, Reward
from backend.app.services.gamification import (
    award_points,
    get_leaderboard,
    get_user_points_summary,
    claim_reward,
    get_claimable_rewards,
    load_rewards_config
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # Create test users
        u1 = User(id=1, name="Ramesh Kumar", email="ramesh@example.com", username="ramesh_k", points=0, role="farmer")
        u2 = User(id=2, name="Priya Patel", email="priya@example.com", username="priya_p", points=40, role="farmer")
        u3 = User(id=3, name="Dr. Swaminathan", email="swami@example.com", username="dr_swami", points=160, role="expert")
        db.add_all([u1, u2, u3])
        db.commit()
    yield


def test_reward_rules_config_loading():
    config = load_rewards_config()
    assert "reward_rules" in config
    rules = config["reward_rules"]
    assert rules["first_disease_in_village"]["points"] == 10
    assert rules["validated_report"]["points"] == 5
    assert rules["share_advisory"]["points"] == 2

    catalog = get_claimable_rewards()
    assert len(catalog) >= 3
    assert any(c["id"] == "voucher_fertilizer_10" for c in catalog)


def test_award_points_rules_and_atomic_persistence():
    # 1. First report in village -> +10 points
    res1 = award_points(user_id=1, reason="first_disease_in_village")
    assert res1["points_added"] == 10
    assert res1["total_points"] == 10

    # 2. Validated report -> +5 points
    res2 = award_points(user_id=1, reason="validated_report")
    assert res2["points_added"] == 5
    assert res2["total_points"] == 15

    # 3. Share advisory -> +2 points
    res3 = award_points(user_id=1, reason="share_advisory")
    assert res3["points_added"] == 2
    assert res3["total_points"] == 17

    # 4. Verify DB persistence
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == 1).first()
        assert user.points == 17
        rewards = db.query(Reward).filter(Reward.user_id == 1).all()
        assert len(rewards) == 3
        points_sum = sum(r.points for r in rewards)
        assert points_sum == 17


def test_award_points_invalid_inputs():
    with pytest.raises(ValueError, match="greater than zero"):
        award_points(user_id=1, reason="bad_points", points=-5)

    with pytest.raises(ValueError, match="not found"):
        award_points(user_id=9999, reason="share_advisory")


def test_leaderboard_service_ranking_and_badges():
    # Award points to make user 1 exceed user 2
    award_points(user_id=1, reason="custom_scouting", points=80)

    leaderboard = get_leaderboard(limit=50)
    assert len(leaderboard) == 3
    # Dr. Swaminathan (160) -> Ramesh Kumar (80) -> Priya Patel (40)
    assert leaderboard[0]["user_id"] == 3
    assert leaderboard[0]["rank"] == 1
    assert "Master Agronomist" in leaderboard[0]["tier"]

    assert leaderboard[1]["user_id"] == 1
    assert leaderboard[1]["rank"] == 2
    assert "Plant Doctor" in leaderboard[1]["tier"]

    assert leaderboard[2]["user_id"] == 2
    assert leaderboard[2]["rank"] == 3
    assert "Eco Scout" in leaderboard[2]["tier"]


def test_gamification_routes_reward_and_action():
    # POST /gamification/reward
    res = client.post("/gamification/reward", json={
        "user_id": 1,
        "points": 50,
        "reason": "Submitted high-accuracy diseased sample"
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["points_added"] == 50
    assert data["total_points"] == 50

    # Negative points check
    bad_res = client.post("/gamification/reward", json={
        "user_id": 1,
        "points": -10,
        "reason": "Invalid"
    })
    assert bad_res.status_code == 400

    # POST /gamification/action for rule-based rewards
    action_res1 = client.post("/gamification/action", json={
        "action": "first_disease_in_village",
        "user_id": 1
    })
    assert action_res1.status_code == 200
    assert action_res1.json()["data"]["points_added"] == 10

    action_res2 = client.post("/gamification/action", json={
        "action": "validated_report",
        "user_id": 1
    })
    assert action_res2.status_code == 200
    assert action_res2.json()["data"]["points_added"] == 5

    action_res3 = client.post("/gamification/action", json={
        "action": "share_advisory",
        "user_id": 1
    })
    assert action_res3.status_code == 200
    assert action_res3.json()["data"]["points_added"] == 2


def test_gamification_leaderboard_route():
    res = client.get("/gamification/leaderboard?limit=50")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "leaderboard" in data
    assert "total_participants" in data
    assert data["limit"] == 50
    assert len(data["leaderboard"]) >= 3


def test_gamification_points_summary_route():
    # Add a transaction for user 2
    client.post("/gamification/reward", json={
        "user_id": 2,
        "points": 25,
        "reason": "Routine scout"
    })

    res = client.get("/gamification/points?user_id=2")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["user_id"] == 2
    assert data["total_points"] == 65
    assert data["badge"] == "🌾 Plant Doctor"
    assert len(data["recent_transactions"]) >= 1


def test_gamification_catalog_and_claim_reward():
    # 1. View Catalog
    catalog_res = client.get("/gamification/catalog")
    assert catalog_res.status_code == 200
    catalog = catalog_res.json()["data"]["catalog"]
    assert len(catalog) >= 3

    # User 3 has 160 points -> Claim 30 points voucher
    claim_res = client.post("/gamification/claim", json={
        "user_id": 3,
        "reward_item_id": "voucher_fertilizer_10"
    })
    assert claim_res.status_code == 200
    claim_data = claim_res.json()["data"]
    assert claim_data["success"] is True
    assert claim_data["points_deducted"] == 30
    assert claim_data["remaining_points"] == 130
    assert claim_data["voucher_code"].startswith("AGRI-")

    # User 1 has 0 points -> Trying to claim 30 points item must fail with 400
    insufficient_res = client.post("/gamification/claim", json={
        "user_id": 1,
        "reward_item_id": "voucher_fertilizer_10"
    })
    assert insufficient_res.status_code == 400
    error_info = insufficient_res.json().get("error", {})
    assert "Insufficient points" in error_info.get("message", "")
