import pytest
import httpx
from backend.app.main import app
from backend.app.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_auth_registration_and_login_flow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a new farmer user
        reg_payload = {
            "name": "Kavita Shinde",
            "email": "kavita.farmer@example.com",
            "password": "FarmPassword123!",
            "phone": "+91 98765 43210",
            "role": "farmer"
        }
        reg_res = await client.post("/auth/register", json=reg_payload)
        assert reg_res.status_code == 200
        reg_data = reg_res.json()
        assert reg_data["success"] is True
        assert reg_data["data"]["email"] == "kavita.farmer@example.com"
        assert reg_data["data"]["role"] == "farmer"

        # 2. Prevent duplicate registration with same email
        dup_res = await client.post("/auth/register", json=reg_payload)
        assert dup_res.status_code == 400
        assert "already registered" in dup_res.json()["error"]["message"].lower()

        # 3. Login with registered credentials
        login_res = await client.post("/auth/login", json={
            "email": "kavita.farmer@example.com",
            "password": "FarmPassword123!"
        })
        assert login_res.status_code == 200
        login_data = login_res.json()
        assert login_data["success"] is True
        access_token = login_data["data"]["access_token"]
        refresh_token = login_data["data"]["refresh_token"]
        assert access_token is not None
        assert refresh_token is not None

        # 4. Login with invalid password fails
        bad_login = await client.post("/auth/login", json={
            "email": "kavita.farmer@example.com",
            "password": "WrongPassword!"
        })
        assert bad_login.status_code in (400, 401)

        # 5. Access protected profile endpoint /auth/me with Bearer token
        me_res = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_res.status_code == 200
        me_data = me_res.json()["data"]
        assert me_data["email"] == "kavita.farmer@example.com"
        assert me_data["role"] == "farmer"

        # 6. Exchange refresh token for new access token
        refresh_res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_res.status_code == 200
        new_tokens = refresh_res.json()["data"]
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

@pytest.mark.anyio
async def test_auth_unauthenticated_access_rejected():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Requesting /auth/me without token returns 401
        res = await client.get("/auth/me")
        assert res.status_code == 401
