import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_app, app
from backend.app.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_app_startup_and_health():
    # 1. Root endpoint assertion
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["status"] == "online"

    # 2. Health endpoint assertion
    health_res = client.get("/health")
    assert health_res.status_code == 200
    health_body = health_res.json()
    assert health_body["success"] is True
    assert health_body["error"] is None
    assert health_body["data"]["status"] == "healthy"

    # 3. Versioned health endpoint assertion
    v1_health = client.get("/api/v1/health")
    assert v1_health.status_code == 200
    v1_body = v1_health.json()
    assert v1_body["success"] is True
    assert v1_body["error"] is None
    assert v1_body["data"]["status"] == "healthy"

def test_app_factory():
    # Test application factory directly
    custom_app = create_app()
    custom_client = TestClient(custom_app)
    response = custom_client.get("/health")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_consistent_error_envelope():
    # Trigger 404
    not_found = client.get("/non-existent-endpoint-404")
    assert not_found.status_code == 404
    body = not_found.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == 404
