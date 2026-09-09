import os
import io
import time
import uuid
import hmac
import hashlib
from typing import Union, Optional, Dict, Any, Tuple
from PIL import Image
from fastapi import UploadFile, HTTPException

from backend.app.config import settings
from backend.app.utils.logger import logger

# Base storage directories
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STORAGE_DIR = os.path.join(BACKEND_DIR, "storage")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
OVERLAYS_DIR = os.path.join(STORAGE_DIR, "overlays")
THUMBNAILS_DIR = os.path.join(STORAGE_DIR, "thumbnails")

for d in (UPLOADS_DIR, OVERLAYS_DIR, THUMBNAILS_DIR):
    os.makedirs(d, exist_ok=True)

# Allowed image formats & extensions
ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "BMP"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class StoredImage(str):
    """
    Subclass of str representing the file path or S3 key,
    while carrying rich attributes (public_url, thumbnail_path, etc.)
    """
    path: str
    public_url: str
    thumbnail_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    optimized_path: Optional[str] = None
    optimized_url: Optional[str] = None
    filename: str = ""
    file_size: int = 0
    storage_backend: str = "local"

    def __new__(cls, path: str, **kwargs):
        obj = super().__new__(cls, path)
        obj.path = path
        for k, v in kwargs.items():
            setattr(obj, k, v)
        return obj

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self),
            "public_url": getattr(self, "public_url", str(self)),
            "thumbnail_path": getattr(self, "thumbnail_path", None),
            "thumbnail_url": getattr(self, "thumbnail_url", None),
            "optimized_path": getattr(self, "optimized_path", None),
            "optimized_url": getattr(self, "optimized_url", None),
            "filename": getattr(self, "filename", ""),
            "file_size": getattr(self, "file_size", 0),
            "storage_backend": getattr(self, "storage_backend", "local")
        }


def _get_s3_client():
    """Create boto3 S3 client if S3 is configured, else return None."""
    if not settings.S3_BUCKET_NAME:
        return None
    try:
        import boto3
        client_kwargs = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        return boto3.client("s3", **client_kwargs)
    except Exception as e:
        logger.warning(f"Failed to initialize S3 client: {e}")
        return None


def validate_image(image_bytes: bytes, filename: Optional[str] = None) -> Image.Image:
    """
    Validate image file size, extension, and integrity.
    Returns loaded PIL Image in RGB format.
    """
    # 1. Size Validation
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image size ({len(image_bytes) / 1024 / 1024:.2f}MB) exceeds maximum limit of {settings.MAX_IMAGE_SIZE_MB}MB"
        )

    # 2. Extension Validation (if filename provided)
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

    # 3. Content / Magic Bytes Integrity Validation
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        fmt = (pil_img.format or "").upper()
        if fmt not in ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format '{fmt}'. Allowed formats: JPEG, PNG, WEBP, BMP"
            )
        # Verify image stream integrity
        pil_img.verify()
        # Re-open for transformation since verify() closes/empties stream
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return pil_img
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Corrupt or unreadable image file: {str(e)}")


def generate_public_url(path: str) -> str:
    """
    Generate public HTTP access URL for a given image path or S3 key.
    """
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path

    # If S3 is configured and path is an S3 key
    s3_client = _get_s3_client()
    if s3_client and not os.path.isabs(path) and ("/" in path or "\\" in path):
        key = path.replace("\\", "/").lstrip("/")
        return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

    # Local Storage URL mapping
    norm_path = os.path.abspath(path)
    if norm_path.startswith(STORAGE_DIR):
        rel = os.path.relpath(norm_path, STORAGE_DIR).replace("\\", "/")
        return f"/storage/{rel}"

    # Default fallback
    base_name = os.path.basename(path)
    return f"/storage/uploads/{base_name}"


def generate_signed_url(path_or_key: str, expiration_seconds: int = 3600) -> str:
    """
    Generate a signed temporary access URL:
    - Pre-signed S3 URL if S3 is active
    - HMAC-signed temporary token URL for local storage
    """
    s3_client = _get_s3_client()
    if s3_client:
        key = path_or_key.replace("\\", "/").lstrip("/")
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
                ExpiresIn=expiration_seconds
            )
            return url
        except Exception as e:
            logger.warning(f"Failed to generate S3 pre-signed URL: {e}")

    # Local signed URL with HMAC expiration signature
    pub_url = generate_public_url(path_or_key)
    expires_at = int(time.time()) + expiration_seconds
    signature_payload = f"{pub_url}:{expires_at}".encode("utf-8")
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), signature_payload, hashlib.sha256).hexdigest()[:16]

    delimiter = "&" if "?" in pub_url else "?"
    return f"{pub_url}{delimiter}expires={expires_at}&signature={sig}"


def save_image(
    file: Union[UploadFile, bytes, io.BytesIO, str],
    subfolder: str = "uploads"
) -> StoredImage:
    """
    Validate, optimize, generate thumbnails, and persist image:
    - Saves locally to /backend/storage/{subfolder} and thumbnails/
    - If S3 is configured, uploads to S3 bucket and returns S3 URL
    - Returns StoredImage instance behaving as a path string with metadata attributes.
    """
    filename = "image.jpg"
    image_bytes = b""

    # 1. Extract bytes and original filename
    if isinstance(file, UploadFile):
        filename = file.filename or "upload.jpg"
        file.file.seek(0)
        image_bytes = file.file.read()
    elif isinstance(file, bytes):
        image_bytes = file
    elif isinstance(file, io.BytesIO):
        image_bytes = file.getvalue()
    elif isinstance(file, str):
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")
        filename = os.path.basename(file)
        with open(file, "rb") as f:
            image_bytes = f.read()
    else:
        raise ValueError(f"Unsupported file type: {type(file)}")

    # 2. Validate Image Content & Dimensions
    pil_img = validate_image(image_bytes, filename=filename)

    # 3. Prepare Unique Names
    stem = f"img_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    main_filename = f"{stem}.jpg"
    thumb_filename = f"{stem}_thumb.jpg"
    opt_filename = f"{stem}_web.jpg"

    target_dir = os.path.join(STORAGE_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    local_main_path = os.path.join(target_dir, main_filename)
    local_thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename)
    local_opt_path = os.path.join(target_dir, opt_filename)

    # 4. Generate Web-Optimized Version (Max 1600x1600, 85% Quality)
    opt_img = pil_img.copy()
    if opt_img.width > 1600 or opt_img.height > 1600:
        opt_img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

    # 5. Generate Thumbnail (256x256)
    thumb_img = pil_img.copy()
    thumb_img.thumbnail((256, 256), Image.Resampling.LANCZOS)

    # 6. Save Local Copies
    pil_img.save(local_main_path, format="JPEG", quality=95)
    opt_img.save(local_opt_path, format="JPEG", quality=85, optimize=True)
    thumb_img.save(local_thumb_path, format="JPEG", quality=85)

    # 7. S3 Upload (if configured)
    s3_client = _get_s3_client()
    if s3_client:
        s3_key_main = f"{subfolder}/{main_filename}"
        s3_key_opt = f"{subfolder}/{opt_filename}"
        s3_key_thumb = f"thumbnails/{thumb_filename}"

        try:
            s3_client.upload_file(local_main_path, settings.S3_BUCKET_NAME, s3_key_main, ExtraArgs={"ContentType": "image/jpeg"})
            s3_client.upload_file(local_opt_path, settings.S3_BUCKET_NAME, s3_key_opt, ExtraArgs={"ContentType": "image/jpeg"})
            s3_client.upload_file(local_thumb_path, settings.S3_BUCKET_NAME, s3_key_thumb, ExtraArgs={"ContentType": "image/jpeg"})

            s3_url_main = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key_main}"
            s3_url_opt = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key_opt}"
            s3_url_thumb = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key_thumb}"

            logger.info(f"Image uploaded to S3: bucket={settings.S3_BUCKET_NAME}, key={s3_key_main}")

            return StoredImage(
                s3_url_main,
                public_url=s3_url_main,
                thumbnail_path=local_thumb_path,
                thumbnail_url=s3_url_thumb,
                optimized_path=local_opt_path,
                optimized_url=s3_url_opt,
                filename=main_filename,
                file_size=len(image_bytes),
                storage_backend="s3"
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {e}. Falling back to local storage.")

    # 8. Local Storage Return
    public_main_url = generate_public_url(local_main_path)
    public_opt_url = generate_public_url(local_opt_path)
    public_thumb_url = generate_public_url(local_thumb_path)

    logger.info(f"Image saved locally: {local_main_path}")

    return StoredImage(
        local_main_path,
        public_url=public_main_url,
        thumbnail_path=local_thumb_path,
        thumbnail_url=public_thumb_url,
        optimized_path=local_opt_path,
        optimized_url=public_opt_url,
        filename=main_filename,
        file_size=len(image_bytes),
        storage_backend="local"
    )
