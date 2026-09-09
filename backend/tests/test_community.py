import io
import time
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.database import Base, engine
from backend.app.models.entities import Report, CommunityTrend
from backend.app.utils.cache import SimpleLRUCache, cache_manager

client = TestClient(app)


def create_test_image_bytes() -> bytes:
    img = Image.new("RGB", (64, 64), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def setup_db():
    cache_manager.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    cache_manager.clear()


def test_post_community_report_json():
    payload = {
        "crop": "Tomato",
        "symptoms": "Brown leaf spots and curling",
        "location": "Guntur District",
        "lat": 16.3067,
        "lng": 80.4365
    }
    response = client.post("/community/report", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    report = data["data"]
    assert report["crop_type"] == "Tomato"
    assert report["symptoms"] == "Brown leaf spots and curling"
    assert report["location"] == "Guntur District"
    assert report["location_lat"] == 16.3067
    assert report["location_lng"] == 80.4365
    assert report["status"] == "pending"


def test_post_community_report_form_with_image():
    img_bytes = create_test_image_bytes()
    form_data = {
        "crop_type": "Wheat",
        "notes": "Yellow rust pustules on leaf surface",
        "location": "Ludhiana Sector 4",
        "lat": "30.9010",
        "lng": "75.8573"
    }
    files = {
        "image": ("leaf.jpg", img_bytes, "image/jpeg")
    }
    response = client.post("/community/report", data=form_data, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    report = data["data"]
    assert report["crop_type"] == "Wheat"
    assert report["image_url"] is not None
    assert "/storage/uploads/" in report["image_url"]


def test_post_community_report_missing_crop():
    response = client.post("/community/report", json={"notes": "Wilting leaves"})
    assert response.status_code == 400


def test_community_trends_aggregation_and_geojson():
    # 1. Post two reports
    client.post("/community/report", json={
        "crop": "Tomato",
        "symptoms": "Early Blight",
        "location": "Hyderabad Outer Ring",
        "lat": 17.3850,
        "lng": 78.4867
    })
    client.post("/community/report", json={
        "crop": "Tomato",
        "symptoms": "Early Blight",
        "location": "Hyderabad Outer Ring",
        "lat": 17.3850,
        "lng": 78.4867
    })

    # 2. Query trends
    res = client.get("/community/trends")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_reported_cases"] >= 2
    assert "trends" in data
    assert len(data["trends"]) >= 1
    assert "geojson_clusters" in data
    assert data["geojson_clusters"]["type"] == "FeatureCollection"
    assert len(data["geojson_clusters"]["features"]) >= 1

    feature = data["geojson_clusters"]["features"][0]
    assert feature["type"] == "Feature"
    assert "coordinates" in feature["geometry"]
    assert feature["properties"]["disease"] == "Early Blight"


def test_community_trends_filters():
    # Post distinct reports
    client.post("/community/report", json={
        "crop": "Rice",
        "symptoms": "Bacterial Leaf Blight",
        "location": "Punjab North",
        "lat": 31.1471,
        "lng": 75.3412
    })
    client.post("/community/report", json={
        "crop": "Cotton",
        "symptoms": "Bollworm Infestation",
        "location": "Telangana South",
        "lat": 16.5000,
        "lng": 78.0000
    })

    # Filter by disease
    res_disease = client.get("/community/trends?disease=Bacterial")
    assert res_disease.status_code == 200
    trends_disease = res_disease.json()["data"]["trends"]
    assert all("Bacterial" in t["disease_name"] for t in trends_disease)

    # Filter by bbox covering Punjab only: min_lng=74, min_lat=30, max_lng=76, max_lat=32
    res_bbox = client.get("/community/trends?bbox=74.0,30.0,76.0,32.0")
    assert res_bbox.status_code == 200
    clusters = res_bbox.json()["data"]["geojson_clusters"]["features"]
    assert len(clusters) == 1
    assert "Bacterial" in clusters[0]["properties"]["disease"]


def test_community_trends_caching():
    cache_manager.clear()
    client.post("/community/report", json={
        "crop": "Maize",
        "symptoms": "Common Rust",
        "location": "Nashik",
        "lat": 19.9975,
        "lng": 73.7898
    })

    # First call: cache miss
    res1 = client.get("/community/trends?disease=Rust")
    assert res1.status_code == 200
    assert res1.json()["data"]["cached"] is False

    # Second call: cache hit
    res2 = client.get("/community/trends?disease=Rust")
    assert res2.status_code == 200
    assert res2.json()["data"]["cached"] is True


def test_community_nearby_reports():
    cache_manager.clear()
    # Report 1: Hyderabad Center (~0 km from center)
    client.post("/community/report", json={
        "crop": "Chili",
        "symptoms": "Leaf Curl",
        "location": "Hyderabad Center",
        "lat": 17.3850,
        "lng": 78.4867
    })

    # Report 2: Near Secunderabad (~10 km away)
    client.post("/community/report", json={
        "crop": "Chili",
        "symptoms": "Anthracnose",
        "location": "Secunderabad",
        "lat": 17.4399,
        "lng": 78.4983
    })

    # Report 3: Bangalore (~500 km away)
    client.post("/community/report", json={
        "crop": "Coffee",
        "symptoms": "Coffee Rust",
        "location": "Bangalore",
        "lat": 12.9716,
        "lng": 77.5946
    })

    # Query within 20 km of Hyderabad
    res = client.get("/community/nearby?lat=17.3850&lng=78.4867&radius=20.0")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["nearby_reports_count"] == 2
    reports = data["reports"]
    assert len(reports) == 2
    # Check sorted by distance
    assert reports[0]["distance_km"] <= reports[1]["distance_km"]
    assert reports[0]["crop_type"] == "Chili"

    # Query with larger radius: all 3 should be included
    res_large = client.get("/community/nearby?lat=17.3850&lng=78.4867&radius=600.0")
    assert res_large.json()["data"]["nearby_reports_count"] == 3


def test_lru_cache_direct():
    lru = SimpleLRUCache(capacity=2, default_ttl=1)
    lru.set("k1", "v1")
    lru.set("k2", "v2")
    assert lru.get("k1") == "v1"

    # Add 3rd item -> k2 should be evicted (k1 was accessed recently)
    lru.set("k3", "v3")
    assert lru.get("k2") is None
    assert lru.get("k1") == "v1"
    assert lru.get("k3") == "v3"

    # Test TTL expiration
    time.sleep(1.1)
    assert lru.get("k1") is None
    assert lru.get("k3") is None
