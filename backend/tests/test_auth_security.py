import io
import uuid
import pytest
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings
from backend.app.database import Base, engine, SessionLocal
from backend.app.models.user import User
from backend.app.utils.security import verify_password, get_password_hash, verify_token
from backend.app.auth.limiter import login_limiter
from backend.app.utils.sanitizer import sanitize_text, sanitize_filename
from backend.app.utils.storage import scan_for_malware_signatures, validate_image

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    login_limiter._failures.clear()
    yield
    Base.metadata.drop_all(bind=engine)


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


def test_security_headers_present():
    """Verify defensive security headers are attached to all responses."""
    response = client.get("/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")


def test_hsts_and_https_enforcement():
    """Verify HSTS header is attached when ENFORCE_HTTPS is True."""
    prev_enforce = settings.ENFORCE_HTTPS
    try:
        settings.ENFORCE_HTTPS = True
        response = client.get("/health", headers={"x-forwarded-proto": "https"})
        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    finally:
        settings.ENFORCE_HTTPS = prev_enforce


def test_secure_cookie_flags_on_login():
    """Verify refresh token cookie is set with HttpOnly, SameSite=lax, and Path=/."""
    uid = uuid.uuid4().hex[:6]
    client.post("/auth/register", json={
        "name": "Secure User",
        "email": f"cookie_user_{uid}@krishi.test",
        "phone": f"+9192{uid[:8]}",
        "username": f"user_{uid}",
        "password": "SecurePassword123!",
        "role": "farmer"
    })

    login_res = client.post("/auth/login", json={
        "username": f"user_{uid}",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    assert "refresh_token" in login_res.cookies

    set_cookie_header = login_res.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header
    assert "samesite=lax" in set_cookie_header.lower()
    assert "Path=/" in set_cookie_header


def test_input_sanitizer():
    """Verify HTML tags, script injection, and control characters are stripped."""
    dirty_text = "<script>alert('pwned')</script>Hello <b>World</b>\x00\x08!"
    clean_text = sanitize_text(dirty_text)
    assert "<script>" not in clean_text
    assert "</script>" not in clean_text
    assert "<b>" not in clean_text
    assert "\x00" not in clean_text
    assert "Hello World!" in clean_text

    dirty_file = "../" + "../../etc/passwd"
    clean_file = sanitize_filename(dirty_file)
    assert "/" not in clean_file
    assert ".." not in clean_file
    assert clean_file == "passwd"

    windows_file = "..\\" + "..\\windows\\system32\\calc.exe"
    clean_win = sanitize_filename(windows_file)
    assert "\\" not in clean_win
    assert ".." not in clean_win
    assert clean_win == "calc.exe"


def test_malware_detection_signatures():
    """Verify executable signatures and embedded web shells are rejected."""
    # PE Header (MZ)
    fake_exe = bytes.fromhex("4d5a900003000000")
    with pytest.raises(HTTPException) as exc_pe:
        scan_for_malware_signatures(fake_exe)
    assert exc_pe.value.status_code == 400
    assert "executable" in exc_pe.value.detail.lower()

    # Linux ELF
    fake_elf = bytes.fromhex("7f454c4602010100")
    with pytest.raises(HTTPException) as exc_elf:
        scan_for_malware_signatures(fake_elf)
    assert exc_elf.value.status_code == 400

    # Embedded script pattern
    polyglot_payload = b"IMG_HEADER_" + bytes.fromhex("3c3f706870") + b" eval($_POST['x']);"
    with pytest.raises(HTTPException) as exc_php:
        scan_for_malware_signatures(polyglot_payload)
    assert exc_php.value.status_code == 400
    assert "forbidden script" in exc_php.value.detail.lower()


def test_valid_image_validation():
    """Verify legitimate images pass validation and return PIL RGB Image."""
    img = Image.new("RGB", (100, 100), color="green")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    valid_bytes = img_byte_arr.getvalue()

    validated_img = validate_image(valid_bytes, filename="leaf.jpg")
    assert validated_img.size == (100, 100)
    assert validated_img.mode == "RGB"

