import os
import io
import pytest
import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal, Base, engine
from backend.app.models.disease_prediction import DiseasePrediction
from ml_model.inference import predict, PlantDiseaseDetector

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def create_sample_leaf_bytes():
    """Create a mock diseased leaf image in bytes."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    img[:, :] = [45, 150, 50]  # Green leaf tone
    # Add necrotic lesion spot
    cv2.circle(img, (150, 150), 40, (135, 80, 25), -1)

    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    return buf.getvalue()


def test_inference_predict_function():
    """Test ml_model/inference.py predict function returns contract schema."""
    sample_bytes = create_sample_leaf_bytes()
    result = predict(sample_bytes)

    assert "disease_name" in result
    assert "confidence" in result
    assert "heatmap_base64" in result
    assert "explanation_text" in result
    assert "top_predictions" in result
    assert "overlay_image_path" in result

    # Check top 3 predictions
    assert len(result["top_predictions"]) >= 3
    for p in result["top_predictions"][:3]:
        assert "disease_name" in p
        assert "confidence" in p
        assert isinstance(p["confidence"], (float, int))

    # Check overlay file existence
    assert os.path.exists(result["overlay_image_path"])
    assert result["heatmap_base64"].startswith("data:image/jpeg;base64,")


def test_deterministic_stub_model():
    """Test deterministic color-thresholding stub works offline without GPU."""
    detector = PlantDiseaseDetector()
    detector.use_stub = True  # Force stub evaluation

    img_rgb = np.zeros((200, 200, 3), dtype=np.uint8)
    img_rgb[:, :] = [40, 160, 45]  # Green
    # Add brown necrosis
    cv2.rectangle(img_rgb, (50, 50), (150, 150), (120, 70, 20), -1)

    stub_out = detector._predict_with_color_thresholding(img_rgb)
    assert len(stub_out["top_predictions"]) >= 3
    assert "Tomato Early Blight" in [p["disease_name"] for p in stub_out["top_predictions"]]
    assert "Color thresholding" in stub_out["explanation"]


def test_ml_proxy_infer_endpoint():
    """Test POST /ml/infer endpoint persists DiseasePrediction and returns contract schema."""
    sample_bytes = create_sample_leaf_bytes()
    files = {"file": ("test_leaf.jpg", sample_bytes, "image/jpeg")}

    response = client.post("/ml/infer", files=files)
    assert response.status_code == 200

    json_resp = response.json()
    assert json_resp["success"] is True
    data = json_resp["data"]

    assert "prediction_id" in data
    assert "disease_name" in data
    assert "confidence" in data
    assert "top_predictions" in data
    assert len(data["top_predictions"]) >= 3
    assert "heatmap_base64" in data
    assert "explanation_text" in data
    assert "overlay_image_path" in data

    # Verify database persistence
    db = SessionLocal()
    try:
        record = db.query(DiseasePrediction).filter(DiseasePrediction.id == data["prediction_id"]).first()
        assert record is not None
        assert record.disease_name == data["disease_name"]
        assert record.confidence == data["confidence"]
        assert record.explanation_text == data["explanation_text"]
    finally:
        db.close()


def test_ml_service_wrapper():
    """Test backend/app/services/ml_service.py wrapper."""
    from backend.app.services.ml_service import ml_service
    sample_bytes = create_sample_leaf_bytes()

    result = ml_service.predict(sample_bytes)
    assert "disease_name" in result
    assert "confidence" in result
    assert result["confidence"] > 0
