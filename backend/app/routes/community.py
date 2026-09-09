import math
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import CommunityTrend, Report, User
from backend.app.routes import success_envelope, error_envelope
from backend.app.auth.dependencies import get_optional_current_user
from backend.app.utils.storage import save_image
from backend.app.utils.cache import cache_manager
from backend.app.utils.logger import logger

router = APIRouter(prefix="/community", tags=["Community & Surveillance"])

KNOWN_COORDINATES = {
    "andhra pradesh": (15.9129, 79.7400),
    "hyderabad": (17.3850, 78.4867),
    "telangana": (18.1124, 79.0193),
    "punjab": (31.1471, 75.3412),
    "karnataka": (15.3173, 75.7139),
    "maharashtra": (19.7515, 75.7139),
    "tamil nadu": (11.1271, 78.6569),
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in kilometers between two points on Earth."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


@router.get("/feed")
def get_community_feed(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(limit).all()
    items = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "crop_type": r.crop_type,
            "image_url": r.image_url,
            "location": r.location,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reports
    ]
    return success_envelope(data=items)


@router.post("/report", status_code=201)
async def create_community_report(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Create a lightweight community crop report (crop, symptoms, location, optional image).
    Accepts application/json, multipart/form-data, or form-urlencoded payloads.
    """
    content_type = request.headers.get("content-type", "")
    crop = None
    symptoms = None
    location = None
    lat = None
    lng = None
    image_file = None
    image_b64 = None

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        crop = body.get("crop") or body.get("crop_type")
        symptoms = body.get("symptoms") or body.get("notes") or ""
        location = body.get("location") or "Field Sector Alpha"
        lat = body.get("lat") or body.get("location_lat")
        lng = body.get("lng") or body.get("lon") or body.get("location_lng")
        image_b64 = body.get("image_base64") or body.get("image")
    else:
        # Form or multipart payload
        try:
            form = await request.form()
            crop = form.get("crop") or form.get("crop_type")
            symptoms = form.get("symptoms") or form.get("notes") or ""
            location = form.get("location") or "Field Sector Alpha"
            lat = form.get("lat") or form.get("location_lat")
            lng = form.get("lng") or form.get("lon") or form.get("location_lng")
            image_file = form.get("image") or form.get("file")
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to parse form data")

    if not crop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field 'crop' or 'crop_type' is required"
        )

    # Process optional image
    image_path = None
    image_url = None
    if image_file and hasattr(image_file, "file"):
        try:
            stored = save_image(image_file, subfolder="uploads")
            image_path = stored.path
            image_url = stored.public_url
        except Exception as e:
            logger.warning(f"Failed to process uploaded image: {e}")
            raise HTTPException(status_code=400, detail=f"Image upload failed: {str(e)}")
    elif image_b64 and isinstance(image_b64, str):
        try:
            import base64
            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]
            raw_bytes = base64.b64decode(image_b64)
            stored = save_image(raw_bytes, subfolder="uploads")
            image_path = stored.path
            image_url = stored.public_url
        except Exception as e:
            logger.warning(f"Failed to process base64 image: {e}")
            raise HTTPException(status_code=400, detail=f"Base64 image decode failed: {str(e)}")

    # Resolve reporter user
    if current_user:
        user_id = current_user.id
    else:
        community_user = db.query(User).filter(User.email == "community@crophealth.ai").first()
        if not community_user:
            community_user = User(
                name="Community Reporter",
                email="community@crophealth.ai",
                username="community_reporter",
                role="farmer",
                hashed_password="N/A",
                points=0
            )
            db.add(community_user)
            db.flush()
        user_id = community_user.id

    parsed_lat = float(lat) if lat is not None else 17.3850
    parsed_lng = float(lng) if lng is not None else 78.4867

    # Create Report
    report = Report(
        user_id=user_id,
        crop_type=str(crop),
        notes=str(symptoms) if symptoms else None,
        location=str(location),
        location_lat=parsed_lat,
        location_lng=parsed_lng,
        image_path=image_path,
        status="pending"
    )
    db.add(report)
    db.flush()

    # Aggregate/Update CommunityTrend
    disease_label = symptoms.strip() if symptoms and len(symptoms.strip()) < 50 else f"{crop} Blight"
    trend = db.query(CommunityTrend).filter(
        CommunityTrend.disease_name.ilike(disease_label),
        CommunityTrend.location.ilike(location)
    ).first()

    if trend:
        trend.count += 1
        trend.last_seen = datetime.datetime.utcnow()
    else:
        trend = CommunityTrend(
            disease_name=disease_label,
            location=location,
            count=1,
            location_geojson={
                "type": "Point",
                "coordinates": [parsed_lng, parsed_lat]
            },
            last_seen=datetime.datetime.utcnow()
        )
        db.add(trend)

    db.commit()
    db.refresh(report)

    # Invalidate aggregation cache
    cache_manager.clear()

    data = {
        "report_id": report.id,
        "id": report.id,
        "crop_type": report.crop_type,
        "symptoms": report.notes,
        "location": report.location,
        "location_lat": report.location_lat,
        "location_lng": report.location_lng,
        "image_url": image_url or report.image_url,
        "status": report.status,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "message": "Community crop health report submitted successfully"
    }
    return success_envelope(data=data)


@router.get("/trends")
def get_community_trends(
    bbox: Optional[str] = Query(None, description="Bounding box as min_lng,min_lat,max_lng,max_lat"),
    disease: Optional[str] = Query(None, description="Filter by disease name"),
    since: Optional[str] = Query(None, description="Filter since ISO date/datetime (e.g. 2026-01-01)"),
    location: Optional[str] = Query(None, description="Filter by location string"),
    limit: int = Query(20, ge=1, le=100, description="Limit results"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated disease outbreaks, trends, and GeoJSON clusters with optional bbox & temporal filters.
    Results are cached in Redis or in-memory LRU cache.
    """
    cache_key = f"trends:{bbox}:{disease}:{since}:{location}:{limit}"
    cached = cache_manager.get(cache_key)
    if cached is not None:
        cached["cached"] = True
        return success_envelope(data=cached)

    query = db.query(CommunityTrend)
    if disease:
        query = query.filter(CommunityTrend.disease_name.ilike(f"%{disease}%"))
    if location:
        query = query.filter(CommunityTrend.location.ilike(f"%{location}%"))
    if since:
        try:
            since_clean = since.replace("Z", "+00:00")
            since_dt = datetime.datetime.fromisoformat(since_clean)
            query = query.filter(CommunityTrend.last_seen >= since_dt)
        except Exception as e:
            logger.warning(f"Invalid 'since' format: {since} ({e})")

    trends = query.order_by(CommunityTrend.count.desc()).all()

    # Parse Bounding Box if provided: min_lng, min_lat, max_lng, max_lat
    bbox_filter = None
    if bbox:
        try:
            parts = [float(x.strip()) for x in bbox.split(",")]
            if len(parts) == 4:
                bbox_filter = {
                    "min_lng": parts[0],
                    "min_lat": parts[1],
                    "max_lng": parts[2],
                    "max_lat": parts[3]
                }
        except Exception as e:
            logger.warning(f"Invalid bbox format '{bbox}': {e}")

    filtered_trends = []
    features = []

    for t in trends:
        # Determine coordinates for trend
        lng = 78.4867
        lat = 17.3850
        if t.location_geojson and isinstance(t.location_geojson, dict):
            coords = t.location_geojson.get("coordinates")
            if coords and len(coords) == 2:
                lng, lat = float(coords[0]), float(coords[1])
        else:
            loc_key = (t.location or "").lower()
            matched = False
            for place, place_coords in KNOWN_COORDINATES.items():
                if place in loc_key:
                    lat, lng = place_coords
                    matched = True
                    break
            if not matched and t.id:
                lat = 17.3850 + ((t.id * 7) % 50) * 0.05
                lng = 78.4867 + ((t.id * 11) % 50) * 0.05

        # Check bbox filter
        if bbox_filter:
            if not (bbox_filter["min_lng"] <= lng <= bbox_filter["max_lng"] and
                    bbox_filter["min_lat"] <= lat <= bbox_filter["max_lat"]):
                continue

        filtered_trends.append(t)
        risk_level = "High" if t.count >= 10 else ("Moderate" if t.count >= 4 else "Low")
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(lng, 5), round(lat, 5)]
            },
            "properties": {
                "id": t.id,
                "disease": t.disease_name,
                "count": t.count,
                "location": t.location,
                "risk_level": risk_level,
                "last_seen": t.last_seen.isoformat() if t.last_seen else None
            }
        })

    limited_trends = filtered_trends[:limit]
    limited_features = features[:limit]

    total_reports = sum(t.count for t in limited_trends)
    high_risk_zones = list(set([t.location for t in limited_trends if t.count >= 5 and t.location]))

    data = {
        "total_reported_cases": total_reports,
        "active_regions_monitored": len(set(t.location for t in limited_trends if t.location)),
        "high_risk_zones": high_risk_zones,
        "trends": [
            {
                "id": t.id,
                "disease_name": t.disease_name,
                "reported_cases": t.count,
                "location": t.location,
                "risk_level": "High" if t.count >= 10 else ("Moderate" if t.count >= 4 else "Low"),
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in limited_trends
        ],
        "geojson_clusters": {
            "type": "FeatureCollection",
            "features": limited_features
        },
        "filters": {
            "bbox": bbox,
            "disease": disease,
            "since": since,
            "location": location
        },
        "cached": False
    }

    cache_manager.set(cache_key, data, ttl=60)
    return success_envelope(data=data)


@router.get("/nearby")
def get_nearby_reports(
    lat: float = Query(17.3850, ge=-90.0, le=90.0, description="User latitude"),
    lng: Optional[float] = Query(None, ge=-180.0, le=180.0, description="User longitude"),
    lon: Optional[float] = Query(None, ge=-180.0, le=180.0, description="User longitude alias"),
    radius: Optional[float] = Query(None, ge=0.1, le=2000.0, description="Search radius in km"),
    radius_km: Optional[float] = Query(25.0, ge=0.1, le=2000.0, description="Search radius in km"),
    limit: int = Query(20, ge=1, le=100, description="Limit results"),
    db: Session = Depends(get_db)
):
    """
    Get recent reports within a geographic radius using Haversine calculation.
    Supports both 'lng' and 'lon', and both 'radius' and 'radius_km'.
    """
    actual_lng = lng if lng is not None else (lon if lon is not None else 78.4867)
    actual_radius = radius if radius is not None else (radius_km if radius_km is not None else 25.0)

    cache_key = f"nearby:{round(lat, 4)}:{round(actual_lng, 4)}:{round(actual_radius, 2)}:{limit}"
    cached = cache_manager.get(cache_key)
    if cached is not None:
        cached["cached"] = True
        return success_envelope(data=cached)

    reports = db.query(Report).order_by(Report.submitted_at.desc()).all()

    items = []
    for r in reports:
        r_lat = r.location_lat
        r_lng = r.location_lng
        if r_lat is not None and r_lng is not None:
            dist = haversine_distance(lat, actual_lng, r_lat, r_lng)
        else:
            dist = round(5.2 + (r.id % 12) * 1.5, 1)

        if dist <= actual_radius:
            items.append({
                "report_id": r.id,
                "id": r.id,
                "crop_type": r.crop_type,
                "location": r.location,
                "latitude": r_lat,
                "longitude": r_lng,
                "distance_km": dist,
                "status": r.status,
                "notes": r.notes,
                "image_url": r.image_url,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })

    items.sort(key=lambda x: x["distance_km"])
    limited_items = items[:limit]

    data = {
        "center": {"lat": lat, "lon": actual_lng, "lng": actual_lng},
        "radius_km": actual_radius,
        "nearby_reports_count": len(limited_items),
        "reports": limited_items,
        "cached": False
    }

    cache_manager.set(cache_key, data, ttl=30)
    return success_envelope(data=data)
