import io
import pytest
import httpx
from PIL import Image
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

def create_mock_leaf_image_bytes():
    file_obj = io.BytesIO()
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    img.save(file_obj, format="JPEG")
    file_obj.seek(0)
    return file_obj.getvalue()

@pytest.mark.anyio
async def test_reports_creation_and_retrieval_flow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create report via JSON endpoint
        create_payload = {
            "crop_type": "Tomato",
            "location": "Nashik Greenhouse Sector B",
            "image_url": "https://storage.crophealth.ai/samples/tomato_early_blight.jpg"
        }
        res = await client.post("/reports/", json=create_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        report_id = data["data"]["id"]
        assert report_id is not None
        assert data["data"]["crop_type"] == "Tomato"
        assert data["data"]["status"] == "pending"

        # 2. Retrieve report by ID
        get_res = await client.get(f"/reports/{report_id}")
        assert get_res.status_code == 200
        get_data = get_res.json()["data"]
        assert get_data["report"]["id"] == report_id
        assert get_data["report"]["location"] == "Nashik Greenhouse Sector B"

        # 3. List reports with pagination
        list_res = await client.get("/reports/list?skip=0&limit=10")
        assert list_res.status_code == 200
        raw_data = list_res.json()["data"]
        list_data = raw_data.get("items", []) if isinstance(raw_data, dict) else raw_data
        assert len(list_data) >= 1
        assert any(r["id"] == report_id for r in list_data)

        # 4. Non-existent report returns 404
        not_found_res = await client.get("/reports/999999")
        assert not_found_res.status_code == 404

@pytest.mark.anyio
async def test_upload_report_multipart_file():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Register and login user to verify points attribution
        await client.post("/auth/register", json={
            "name": "Subhash Rao",
            "email": "subhash@agri.com",
            "password": "Password123!",
            "role": "farmer"
        })
        login_res = await client.post("/auth/login", json={
            "email": "subhash@agri.com",
            "password": "Password123!"
        })
        token = login_res.json()["data"]["access_token"]

        img_bytes = create_mock_leaf_image_bytes()
        files = {
            "file": ("leaf.jpg", img_bytes, "image/jpeg")
        }
        data = {
            "crop_type": "Tomato",
            "location": "Pune Field Plot #12"
        }
        headers = {"Authorization": f"Bearer {token}"}

        upload_res = await client.post("/reports/upload", files=files, data=data, headers=headers)
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        assert upload_data["success"] is True
        resp = upload_data["data"]
        assert "report_id" in resp
        assert "disease_prediction" in resp
        assert resp["points_awarded"] == 20
