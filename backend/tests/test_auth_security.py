import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import Base, engine, SessionLocal
from backend.app.models.user import User
from backend.app.utils.security import verify_password, get_password_hash, verify_token
from backend.app.auth.limiter import login_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.create_all(bind=engine)
    login_limiter._failures.clear()
    yield


def test_register_and_uniqueness_validation():
    """Test user registration with email and phone uniqueness constraints."""
    # 1. Successful registration
    res1 = client.post("/auth/register", json={
        "name": "Kavita Rao",
        "email": "kavita@krishi.org",
        "phone": "+919876543201",
        "username": "kavita_krishi",
        "password": "SecurePassword123!",
        "role": "farmer"
    })
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["email"] == "kavita@krishi.org"
    assert data1["phone"] == "+919876543201"

    # 2. Duplicate Email should fail with 400
    res_dup_email = client.post("/auth/register", json={
        "name": "Different Name",
        "email": "kavita@krishi.org",
        "phone": "+919999999999",
        "username": "unique_user_1",
        "password": "SecurePassword123!"
    })
    assert res_dup_email.status_code == 400
    assert "Email is already registered" in res_dup_email.text

    # 3. Duplicate Phone should fail with 400
    res_dup_phone = client.post("/auth/register", json={
        "name": "Another Name",
        "email": "another@krishi.org",
        "phone": "+919876543201",
        "username": "unique_user_2",
        "password": "SecurePassword123!"
    })
    assert res_dup_phone.status_code == 400
    assert "Phone number is already registered" in res_dup_phone.text


def test_login_and_token_refresh():
    """Test login issuing access and refresh tokens, and exchanging refresh tokens."""
    # Register user
    client.post("/auth/register", json={
        "name": "Devi Prasad",
        "email": "devi@agri.net",
        "phone": "+919876543202",
        "username": "devi_agri",
        "password": "DeviPassword123!",
        "role": "farmer"
    })

    # Login
    login_res = client.post("/auth/login", json={
        "username": "devi_agri",
        "password": "DeviPassword123!"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()["data"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    access_payload = verify_token(tokens["access_token"], expected_type="access")
    assert access_payload["sub"] == "devi_agri"

    refresh_payload = verify_token(tokens["refresh_token"], expected_type="refresh")
    assert refresh_payload["sub"] == "devi_agri"

    # Refresh token endpoint
    refresh_res = client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    assert refresh_res.status_code == 200
    refreshed_data = refresh_res.json()["data"]
    assert "access_token" in refreshed_data
    assert "refresh_token" in refreshed_data

    # Invalid refresh token should fail with 401
    bad_refresh = client.post("/auth/refresh", json={
        "refresh_token": "invalid.jwt.token"
    })
    assert bad_refresh.status_code == 401


def test_role_based_access_control():
    """Test require_role('expert') allows experts and rejects farmers with 403."""
    # 1. Register a Farmer
    client.post("/auth/register", json={
        "name": "Farmer Ramesh",
        "email": "ramesh@farm.org",
        "phone": "+919876543203",
        "username": "farmer_ramesh",
        "password": "FarmerPassword123!",
        "role": "farmer"
    })
    farmer_login = client.post("/auth/login", json={
        "username": "farmer_ramesh",
        "password": "FarmerPassword123!"
    })
    farmer_token = farmer_login.json()["data"]["access_token"]
    farmer_headers = {"Authorization": f"Bearer {farmer_token}"}

    # 2. Register an Expert
    client.post("/auth/register", json={
        "name": "Dr. Ananya Sen",
        "email": "ananya@agronomy.ac.in",
        "phone": "+919876543204",
        "username": "expert_ananya",
        "password": "ExpertPassword123!",
        "role": "expert"
    })
    expert_login = client.post("/auth/login", json={
        "username": "expert_ananya",
        "password": "ExpertPassword123!"
    })
    expert_token = expert_login.json()["data"]["access_token"]
    expert_headers = {"Authorization": f"Bearer {expert_token}"}

    # Create dummy report to validate
    from backend.app.models.report import Report
    db = SessionLocal()
    rep = Report(
        user_id=1,
        crop_type="Tomato",
        location="Greenhouse Alpha",
        status="pending"
    )
    db.add(rep)
    db.commit()
    report_id = rep.id
    db.close()

    # Farmer accessing strictly role-guarded expert review endpoint -> 403 Forbidden
    farmer_attempt = client.post("/expert/review", json={
        "report_id": report_id,
        "status": "approved"
    }, headers=farmer_headers)
    assert farmer_attempt.status_code == 403

    # Expert accessing expert review endpoint -> 200 OK
    expert_attempt = client.post("/expert/review", json={
        "report_id": report_id,
        "status": "approved",
        "expert_notes": "Leaf curl virus symptom identified"
    }, headers=expert_headers)
    assert expert_attempt.status_code == 200


def test_in_memory_login_rate_limiter():
    """Test in-memory rate limiter blocks excessive failed login attempts with 429."""
    # Attempt 5 wrong passwords from same client
    for i in range(5):
        fail_res = client.post("/auth/login", json={
            "username": "nonexistent_user",
            "password": f"WrongPass{i}!"
        })
        assert fail_res.status_code in (400, 401)

    # 6th attempt should be blocked with 429 Too Many Requests
    blocked_res = client.post("/auth/login", json={
        "username": "nonexistent_user",
        "password": "WrongPasswordAgain!"
    })
    assert blocked_res.status_code == 429
    assert "Too many failed login attempts" in blocked_res.text


def test_logout():
    """Test user logout endpoint."""
    logout_res = client.post("/auth/logout")
    assert logout_res.status_code == 200
    assert "successfully logged out" in logout_res.text
