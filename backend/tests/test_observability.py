import json
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.utils.logger import logger, setup_logger


@pytest.mark.anyio
async def test_health_liveness_probe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"


@pytest.mark.anyio
async def test_readiness_probe():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "ready"
        assert data["data"]["checks"]["database"] == "ready"
        assert data["data"]["checks"]["storage"] == "ready"


@pytest.mark.anyio
async def test_prometheus_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger an endpoint first
        await client.get("/health")

        # Fetch metrics
        response = await client.get("/metrics")
        assert response.status_code == 200
        metrics_text = response.text
        assert "crophealth_http_requests_total" in metrics_text
        assert "crophealth_http_request_duration_seconds" in metrics_text
        assert "crophealth_http_active_requests" in metrics_text


def test_structured_json_logger(capsys):
    test_logger = setup_logger("TestLogger")
    test_logger.info("Observability verification message", extra={"crop": "Tomato", "stage": "Vegetative"})
    # Verify logger instance exists and has handlers
    assert len(test_logger.handlers) >= 1
