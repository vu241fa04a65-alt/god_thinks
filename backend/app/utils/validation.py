import re
from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_MB = 10

def validate_image_file(file: UploadFile) -> None:
    filename = file.filename or ""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image extension '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

def validate_coordinates(lat: float | None, lon: float | None) -> None:
    if lat is not None and not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90 degrees.")
    if lon is not None and not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180 degrees.")
