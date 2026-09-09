import os
import io
import pytest
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings
from backend.app.utils.storage import (
    save_image,
    generate_public_url,
    generate_signed_url,
    validate_image,
    UPLOADS_DIR,
    THUMBNAILS_DIR
)

client = TestClient(app)


def make_test_image_bytes(width: int = 800, height: int = 600, color: str = "green", format: str = "JPEG") -> bytes:
    """Helper to generate in-memory valid image bytes."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_save_image_local_and_thumbnails():
    """Test local image persistence, thumbnail generation, and web-optimization."""
    data = make_test_image_bytes(width=1800, height=1200, color="forestgreen")
    stored = save_image(data, subfolder="uploads")

    # String behavior & path
    assert isinstance(stored, str)
    assert os.path.exists(str(stored))
    assert stored.storage_backend == "local"

    # Main file, thumbnail, and web-optimized file verification
    assert os.path.exists(stored.thumbnail_path)
    assert os.path.exists(stored.optimized_path)
    assert stored.thumbnail_path.startswith(THUMBNAILS_DIR)

    # Verify thumbnail dimensions (max 256)
    thumb_img = Image.open(stored.thumbnail_path)
    assert thumb_img.width <= 256 and thumb_img.height <= 256

    # Verify optimized dimensions (max 1600)
    opt_img = Image.open(stored.optimized_path)
    assert opt_img.width <= 1600 and opt_img.height <= 1600

    # Verify URLs
    assert stored.public_url.startswith("/storage/uploads/")
    assert stored.thumbnail_url.startswith("/storage/thumbnails/")


def test_generate_public_and_signed_url():
    """Test public URL resolution and signed temporary URL creation."""
    data = make_test_image_bytes(width=300, height=300, color="blue")
    stored = save_image(data, subfolder="uploads")

    # Generate public URL
    pub_url = generate_public_url(stored)
    assert pub_url == stored.public_url

    # Generate signed URL
    signed_url = generate_signed_url(stored, expiration_seconds=600)
    assert pub_url in signed_url
    assert "expires=" in signed_url
    assert "signature=" in signed_url


def test_validation_rejects_corrupted_or_invalid_format():
    """Test validator rejects non-image or corrupted data."""
    # Disguised non-image text
    corrupted_data = b"This is not a real image at all."
    with pytest.raises(HTTPException) as exc_info:
        validate_image(corrupted_data, filename="fake.jpg")
    assert exc_info.value.status_code == 400

    # Empty payload
    with pytest.raises(HTTPException) as exc_empty:
        validate_image(b"")
    assert exc_empty.value.status_code == 400


def test_validation_rejects_oversized_images(monkeypatch):
    """Test validator enforces size limits."""
    # Temporarily set limit to 1 KB to test rejection
    monkeypatch.setattr(settings, "MAX_IMAGE_SIZE_MB", 0.001)
    data = make_test_image_bytes(width=1000, height=1000)
    with pytest.raises(HTTPException) as exc_info:
        validate_image(data, filename="large.jpg")
    assert exc_info.value.status_code == 400
    assert "exceeds maximum limit" in exc_info.value.detail


def test_static_file_serving_via_fastapi():
    """Test that saved images are accessible via the FastAPI mounted /storage endpoint."""
    data = make_test_image_bytes(width=200, height=200, color="orange")
    stored = save_image(data, subfolder="uploads")

    # Access through HTTP client
    response = client.get(stored.public_url)
    assert response.status_code == 200
    assert response.headers["content-type"] in ("image/jpeg", "image/jpg")
    assert len(response.content) > 0


def test_s3_configuration_mock(monkeypatch):
    """Test S3 logic path when S3 settings are configured."""
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", "crophealth-test-bucket")
    monkeypatch.setattr(settings, "AWS_ACCESS_KEY_ID", "TEST_KEY")
    monkeypatch.setattr(settings, "AWS_SECRET_ACCESS_KEY", "TEST_SECRET")
    monkeypatch.setattr(settings, "AWS_REGION", "ap-south-1")

    # Generate public URL for an S3 key
    s3_key = "uploads/leaf_sample.jpg"
    s3_public = generate_public_url(s3_key)
    assert "crophealth-test-bucket.s3.ap-south-1.amazonaws.com" in s3_public
    assert "uploads/leaf_sample.jpg" in s3_public
