# CropHealthAI RESTful API Specification (v1.0.0)

Welcome to the **CropHealthAI RESTful API** documentation. CropHealthAI provides production-grade endpoints for agricultural disease classification, Grad-CAM visual cues, localized pest management advisories, expert validation, gamification, community hotspot tracking, weather risk forecasting, and offline synchronization.

---

## 1. Architectural Conventions

### Base URL & Interactive Docs
- **Base API Prefix**: `/api/v1`
- **Production Base URL**: `https://api.crophealthai.com/api/v1`
- **Local Development URL**: `http://localhost:8000/api/v1`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc Interactive Spec**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`

### Authentication & Authorization
CropHealthAI employs stateless JSON Web Tokens (JWT) along with hardened HTTP cookies:
- **Authorization Header**: `Authorization: Bearer <ACCESS_TOKEN>`
- **Refresh Token Cookie**: Attached automatically upon login with `HttpOnly=True`, `SameSite=Lax`, `Path=/`, and `Secure=True` in production.
- **Roles & Permissions**:
  - `farmer` / `user`: Standard field access (reporting, community, advisory, rewards).
  - `expert`: Certified agronomist role required to review and validate predictions (`@require_role("expert")`).
  - `admin`: Full administrative access.

### Standard Response Envelope
All API responses strictly adhere to the unified response contract:

#### Success Envelope (`200 OK`, `201 Created`)
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

#### Error Envelope (`400`, `401`, `403`, `404`, `422`, `429`, `500`)
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Human-readable explanation of the error",
    "code": 404,
    "details": null
  }
}
```

### Defensive Headers & Rate Limiting
All responses return defensive HTTP headers and sliding-window rate limit metadata:
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 119
X-RateLimit-Reset: 60
```

---

## 2. API Endpoint Directory

| Category | Method | Path | Description | Access |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new user (farmer or expert) | Public |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate credentials & issue tokens | Public |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Refresh access token using cookie or body | Public |
| **Auth** | `POST` | `/api/v1/auth/logout` | Invalidate session & clear cookies | Public |
| **Reports** | `POST` | `/api/v1/reports/upload` | Upload crop leaf image & trigger diagnosis | Authenticated |
| **Reports** | `GET` | `/api/v1/reports/` | List submitted scouting reports | Authenticated |
| **Reports** | `GET` | `/api/v1/reports/{id}` | Retrieve report details with Grad-CAM overlay | Authenticated |
| **Expert** | `GET` | `/api/v1/expert/pending` | List pending predictions awaiting review | Expert Role |
| **Expert** | `POST` | `/api/v1/expert/validate` | Approve or reject a model prediction | Expert Role |
| **Expert** | `GET` | `/api/v1/expert/audit-trail`| Retrieve immutable audit logs of reviews | Expert Role |
| **Community** | `POST` | `/api/v1/community/report` | Submit lightweight community disease sighting | Public |
| **Community** | `GET` | `/api/v1/community/trends` | GeoJSON cluster aggregation of outbreaks | Public |
| **Community** | `GET` | `/api/v1/community/nearby` | Query active reports within radius | Public |
| **Gamification**| `GET` | `/api/v1/gamification/points`| Get user points balance & reward ledger | Authenticated |
| **Gamification**| `GET` | `/api/v1/gamification/leaderboard` | Get regional leaderboard rankings & badges | Public |
| **Gamification**| `GET` | `/api/v1/gamification/catalog` | Get list of redeemable agricultural vouchers | Public |
| **Gamification**| `POST` | `/api/v1/gamification/claim` | Redeem points for farming reward items | Authenticated |
| **Weather** | `GET` | `/api/v1/weather/risk` | 3-day weather risk forecast by location & crop | Public |
| **Advisory** | `GET` | `/api/v1/advisory/recommend`| Ranked bio & eco-friendly IPM recommendations | Public |
| **Advisory** | `GET` | `/api/v1/advisory/restrictions`| Regional banned/restricted pesticide registry | Public |
| **Advisory** | `GET` | `/api/v1/advisory/search` | Search pesticide and bio-control catalog | Public |
| **Alerts** | `POST` | `/api/v1/alerts/subscribe` | Subscribe to SMS outbreak alerts | Authenticated |
| **Alerts** | `POST` | `/api/v1/alerts/unsubscribe`| Unsubscribe from SMS alerts | Authenticated |
| **Alerts** | `POST` | `/api/v1/alerts/sms` | Broadcast geo-fenced outbreak SMS alert | Expert / Admin |
| **Sync** | `POST` | `/api/v1/sync/batch` | Batch sync offline scouting reports | Public / Auth |
| **Sync** | `GET` | `/api/v1/sync/device-status/{id}`| Query device synchronization status | Public |
| **ML Inference**| `POST`| `/api/v1/ml/infer` | Direct Grad-CAM explainability inference | Public |
| **Chatbot** | `POST` | `/api/v1/chatbot/advice` | Multilingual agronomy assistant | Public |
| **Probes** | `GET` | `/health` | Liveness health check probe | Public |
| **Probes** | `GET` | `/ready` | Readiness probe (DB & storage status) | Public |
| **Telemetry** | `GET` | `/metrics` | Prometheus metrics scrape endpoint | Public |

---

## 3. Detailed Endpoint Reference

### 3.1 Authentication

#### `POST /api/v1/auth/register`
Registers a new user account with unique email and phone validation.

- **Request Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "name": "Ramesh Patel",
  "email": "ramesh.patel@kisan.in",
  "phone": "+919876543210",
  "username": "ramesh_patel",
  "password": "FarmerPassword123!",
  "role": "farmer"
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ramesh Patel",
    "email": "ramesh.patel@kisan.in",
    "phone": "+919876543210",
    "username": "ramesh_patel",
    "password": "FarmerPassword123!",
    "role": "farmer"
  }'
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Ramesh Patel",
    "username": "ramesh_patel",
    "email": "ramesh.patel@kisan.in",
    "phone": "+919876543210",
    "role": "farmer",
    "points": 0,
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "error": null
}
```

---

#### `POST /api/v1/auth/login`
Authenticates credentials, issues access/refresh tokens, and sets a secure `HttpOnly` refresh token cookie.

- **Request Body**:
```json
{
  "username": "ramesh_patel",
  "password": "FarmerPassword123!"
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "ramesh_patel", "password": "FarmerPassword123!"}' \
  -c cookies.txt
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "name": "Ramesh Patel",
      "username": "ramesh_patel",
      "email": "ramesh.patel@kisan.in",
      "phone": "+919876543210",
      "role": "farmer",
      "points": 0
    }
  },
  "error": null
}
```

---

#### `POST /api/v1/auth/refresh`
Exchanges a valid refresh token (from body, header, or cookie) for a newly minted access token and rotated cookie.

- **Request Body** (optional if cookie present):
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "error": null
}
```

---

#### `POST /api/v1/auth/logout`
Terminates session and invalidates the secure refresh token cookie.

- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -b cookies.txt
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "message": "User successfully logged out"
  },
  "error": null
}
```

---

### 3.2 Crop Reports & AI Diagnosis

#### `POST /api/v1/reports/upload`
Uploads a foliage image, scans for malware signatures, computes Grad-CAM explainability heatmap, generates localized treatment advisory, and awards scouting points.

- **Request Format**: `multipart/form-data`
- **Parameters**:
  - `file` (File, required): Image file (JPEG, PNG, WEBP, BMP, max 10MB).
  - `crop_type` (string, optional): e.g. "Tomato", "Potato", "Corn".
  - `latitude` (float, optional): e.g. 19.0760.
  - `longitude` (float, optional): e.g. 72.8777.
  - `language` (string, optional): Preferred language code (default "en", supports "hi", "te", "mr", "ta").
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/upload" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@tomato_early_blight.jpg" \
  -F "crop_type=Tomato" \
  -F "latitude=19.0760" \
  -F "longitude=72.8777" \
  -F "language=hi"
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": 101,
    "crop_type": "Tomato",
    "disease_name": "Tomato Early Blight",
    "confidence": 0.942,
    "severity": "Moderate",
    "status": "pending",
    "image_url": "/storage/uploads/img_1725890000_a1b2c3d4.jpg",
    "thumbnail_url": "/storage/thumbnails/img_1725890000_a1b2c3d4_thumb.jpg",
    "overlay_url": "/storage/overlays/img_1725890000_a1b2c3d4_gradcam.jpg",
    "location": "19.0760, 72.8777",
    "points_awarded": 10,
    "advisory": {
      "summary": "टमाटर के अगेती झुलसा (Early Blight) के लक्षण मिले हैं।",
      "treatment": "जैविक फफूंदनाशी ट्राइकोडर्मा विरिडी 5 ग्राम प्रति लीटर पानी में छिड़कें।",
      "eco_friendly": true,
      "pre_harvest_interval_days": 3,
      "safety_notes": "सुरक्षा चश्मा और दस्ताने पहनकर छिड़काव करें।"
    },
    "created_at": "2026-09-09T18:45:00Z"
  },
  "error": null
}
```

---

#### `GET /api/v1/reports/{id}`
Fetches full details of an existing crop scout report including diagnosis, Grad-CAM heatmap, and expert review status.

- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/reports/101" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 101,
    "user_id": 1,
    "crop_type": "Tomato",
    "disease_name": "Tomato Early Blight",
    "confidence": 0.942,
    "status": "pending",
    "image_url": "/storage/uploads/img_1725890000_a1b2c3d4.jpg",
    "overlay_url": "/storage/overlays/img_1725890000_a1b2c3d4_gradcam.jpg",
    "expert_notes": null,
    "validated_by": null,
    "created_at": "2026-09-09T18:45:00Z"
  },
  "error": null
}
```

---

### 3.3 Expert Validation Portal

#### `GET /api/v1/expert/pending`
Retrieves reports awaiting agronomist review. Restricted to users with `role: expert`.

- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/expert/pending?limit=20" \
  -H "Authorization: Bearer <EXPERT_ACCESS_TOKEN>"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "count": 1,
    "items": [
      {
        "id": 101,
        "crop_type": "Tomato",
        "disease_name": "Tomato Early Blight",
        "confidence": 0.942,
        "image_url": "/storage/uploads/img_1725890000_a1b2c3d4.jpg",
        "thumbnail_url": "/storage/thumbnails/img_1725890000_a1b2c3d4_thumb.jpg",
        "overlay_url": "/storage/overlays/img_1725890000_a1b2c3d4_gradcam.jpg",
        "submitted_by": "Ramesh Patel",
        "location": "19.0760, 72.8777",
        "created_at": "2026-09-09T18:45:00Z"
      }
    ]
  },
  "error": null
}
```

---

#### `POST /api/v1/expert/validate`
Allows an agronomist to approve or reject an AI diagnosis. Automatically awards verification bonus points to the original reporter upon approval.

- **Request Body**:
```json
{
  "report_id": 101,
  "status": "approved",
  "expert_notes": "Concentric rings confirmed on lower foliage. Prescribed bio-fungicide is appropriate.",
  "corrected_disease": null
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/expert/validate" \
  -H "Authorization: Bearer <EXPERT_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 101,
    "status": "approved",
    "expert_notes": "Concentric rings confirmed on lower foliage. Prescribed bio-fungicide is appropriate."
  }'
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "report_id": 101,
    "status": "approved",
    "expert_id": 2,
    "bonus_points_awarded": 20,
    "audit_trail_id": 501,
    "message": "Report successfully validated and points awarded to farmer."
  },
  "error": null
}
```

---

#### `GET /api/v1/expert/audit-trail`
Returns immutable audit logs tracking expert approvals, rejections, and corrective notes.

- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/expert/audit-trail?report_id=101" \
  -H "Authorization: Bearer <EXPERT_ACCESS_TOKEN>"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "total": 1,
    "logs": [
      {
        "id": 501,
        "report_id": 101,
        "expert_username": "dr_ananya_sen",
        "action": "approve",
        "notes": "Concentric rings confirmed on lower foliage. Prescribed bio-fungicide is appropriate.",
        "timestamp": "2026-09-09T18:50:00Z"
      }
    ]
  },
  "error": null
}
```

---

### 3.4 Community Surveillance & Outbreak Maps

#### `GET /api/v1/community/trends`
Provides GeoJSON FeatureCollection clustering outbreak hotspots with risk classification.

- **Query Parameters**:
  - `crop_type` (string, optional): Filter by crop.
  - `days` (int, default 14): Historical window.
- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/community/trends?crop_type=Tomato&days=7"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [72.8777, 19.0760]
        },
        "properties": {
          "cluster_id": "cluster_west_01",
          "crop_type": "Tomato",
          "dominant_disease": "Tomato Early Blight",
          "case_count": 14,
          "risk_level": "high",
          "radius_km": 25.0,
          "last_detected": "2026-09-09T18:45:00Z"
        }
      }
    ]
  },
  "error": null
}
```

---

#### `GET /api/v1/community/nearby`
Queries active disease reports within a defined radius of coordinates.

- **Query Parameters**:
  - `lat` (float, required): Latitude.
  - `lon` (float, required): Longitude.
  - `radius_km` (float, default 25.0): Search radius.
- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/community/nearby?lat=19.0760&lon=72.8777&radius_km=30"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "total_nearby": 3,
    "reports": [
      {
        "id": 101,
        "disease": "Tomato Early Blight",
        "distance_km": 2.4,
        "severity": "Moderate",
        "reported_at": "2026-09-09T18:45:00Z"
      }
    ]
  },
  "error": null
}
```

---

### 3.5 Gamification & Rewards

#### `GET /api/v1/gamification/points`
Returns the authenticated farmer's point balance, recent reward ledger entries, and unlocked badges.

- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/gamification/points" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "total_points": 30,
    "level": "Silver Scout",
    "next_level_points": 100,
    "badges": [
      {
        "id": "first_scout",
        "name": "First Foliage Scout",
        "icon": "🌱",
        "awarded_at": "2026-09-09T18:45:00Z"
      },
      {
        "id": "expert_verified",
        "name": "Expert Verified",
        "icon": "🏅",
        "awarded_at": "2026-09-09T18:50:00Z"
      }
    ],
    "history": [
      {
        "id": 1,
        "action": "CROP_SCOUT_UPLOAD",
        "points": 10,
        "description": "Uploaded Tomato scout report #101",
        "created_at": "2026-09-09T18:45:00Z"
      },
      {
        "id": 2,
        "action": "EXPERT_VERIFICATION_BONUS",
        "points": 20,
        "description": "Agronomist approved report #101",
        "created_at": "2026-09-09T18:50:00Z"
      }
    ]
  },
  "error": null
}
```

---

#### `GET /api/v1/gamification/leaderboard`
Returns top ranked farmers in the region sorted by monthly contributions.

- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/gamification/leaderboard?limit=10"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "region": "Western Region",
    "rankings": [
      {
        "rank": 1,
        "user_id": 1,
        "name": "Ramesh Patel",
        "points": 140,
        "verified_reports": 6,
        "badge": "Master Agronomist"
      },
      {
        "rank": 2,
        "user_id": 5,
        "name": "Kavita Rao",
        "points": 110,
        "verified_reports": 4,
        "badge": "Gold Scout"
      }
    ]
  },
  "error": null
}
```

---

#### `POST /api/v1/gamification/claim`
Redeems points for bio-fertilizer vouchers, seed kits, or discount coupons.

- **Request Body**:
```json
{
  "reward_id": "voucher_bio_fert_100",
  "points_required": 25
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/gamification/claim" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reward_id": "voucher_bio_fert_100", "points_required": 25}'
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "claim_id": "claim_78912",
    "voucher_code": "BIO-FERT-2026-XP",
    "remaining_points": 5,
    "expiry_date": "2026-12-31T23:59:59Z"
  },
  "error": null
}
```

---

### 3.6 Integrated Pest Management (IPM) Advisory

#### `GET /api/v1/advisory/recommend`
Generates prioritized treatment protocols favoring biological controls, calculating Pre-Harvest Intervals (PHI), and checking regional chemical bans.

- **Query Parameters**:
  - `disease` (string, required): e.g. "Early Blight".
  - `crop` (string, required): e.g. "Tomato".
  - `region` (string, optional): e.g. "kerala", "punjab", "eu".
  - `language` (string, optional): e.g. "hi", "te", "en".
- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/advisory/recommend?disease=Early+Blight&crop=Tomato&region=kerala&language=hi"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "crop": "Tomato",
    "disease": "Early Blight",
    "region": "kerala",
    "recommendations": [
      {
        "name": "ट्राइकोडर्मा विरिडी (Trichoderma viride)",
        "category": "Biological",
        "eco_friendly": true,
        "dosage": "5 ग्राम / लीटर",
        "pre_harvest_interval_days": 1,
        "safety_notes": "पर्यावरण के अनुकूल, मधुमक्खियों के लिए सुरक्षित।",
        "restrictions_warning": null
      },
      {
        "name": "कॉपर ऑक्सीक्लोराइड (Copper Oxychloride)",
        "category": "Inorganic Fungicide",
        "eco_friendly": false,
        "dosage": "2.5 ग्राम / लीटर",
        "pre_harvest_interval_days": 7,
        "safety_notes": "फसल कटाई से कम से कम 7 दिन पहले छिड़काव बंद करें।",
        "restrictions_warning": "केरल क्षेत्र में प्रतिबंधित रसायनों की सूची अवश्य जांचें।"
      }
    ]
  },
  "error": null
}
```

---

### 3.7 Weather Risk Assessment

#### `GET /api/v1/weather/risk`
Calculates 3-day disease outbreak probability based on humidity, temperature, and leaf wetness duration.

- **Query Parameters**:
  - `lat` (float, required): Latitude.
  - `lon` (float, required): Longitude.
  - `crop` (string, optional): Crop type (default "Tomato").
- **Sample cURL**:
```bash
curl -X GET "http://localhost:8000/api/v1/weather/risk?lat=19.0760&lon=72.8777&crop=Tomato"
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "location": "19.0760, 72.8777",
    "crop": "Tomato",
    "overall_risk": "HIGH",
    "risk_score": 0.82,
    "conditions": {
      "temperature_c": 26.4,
      "relative_humidity_pct": 88,
      "rainfall_mm": 12.5,
      "consecutive_wet_hours": 9
    },
    "preventive_actions": [
      "Improve drainage in furrows to avoid standing water.",
      "Apply preventative bio-agent spray before heavy rain forecast.",
      "Prune lower foliage touching damp soil."
    ]
  },
  "error": null
}
```

---

### 3.8 Alerts & SMS Broadcast

#### `POST /api/v1/alerts/subscribe`
Enables SMS outbreak notifications for a farmer with preferred language and geo-fence perimeter.

- **Request Body**:
```json
{
  "phone_number": "+919876543210",
  "preferred_language": "hi",
  "geofence_radius_km": 25,
  "crop_types": ["Tomato", "Potato"]
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/alerts/subscribe" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "preferred_language": "hi",
    "geofence_radius_km": 25,
    "crop_types": ["Tomato", "Potato"]
  }'
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "status": "subscribed",
    "phone_number": "+919876543210",
    "geofence_radius_km": 25,
    "confirmation_sms_sent": true,
    "message": "SMS alert preferences successfully updated."
  },
  "error": null
}
```

---

### 3.9 Offline Scouting & Batch Sync

#### `POST /api/v1/sync/batch`
Synchronizes an array of offline scouting reports captured on mobile devices in low-connectivity rural zones.

- **Request Body**:
```json
{
  "device_id": "scout_device_pixel_8a",
  "reports": [
    {
      "client_uuid": "offline_rep_99182",
      "crop_type": "Tomato",
      "disease_name": "Tomato Early Blight",
      "latitude": 19.0760,
      "longitude": 72.8777,
      "timestamp": "2026-09-09T17:15:00Z"
    }
  ]
}
```
- **Sample cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/sync/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "scout_device_pixel_8a",
    "reports": [
      {
        "client_uuid": "offline_rep_99182",
        "crop_type": "Tomato",
        "disease_name": "Tomato Early Blight",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "timestamp": "2026-09-09T17:15:00Z"
      }
    ]
  }'
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "synced_count": 1,
    "failed_ids": [],
    "total_points_awarded": 10,
    "message": "Batch synchronization completed successfully."
  },
  "error": null
}
```

---

### 3.10 Health & Monitoring Probes

#### `GET /health`
Liveness probe checking basic service uptime.

- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2026-09-09T19:00:00Z"
  },
  "error": null
}
```

---

#### `GET /ready`
Readiness probe verifying operational status of downstream database and storage engines.

- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "status": "ready",
    "checks": {
      "database": "ready",
      "storage": "ready"
    }
  },
  "error": null
}
```

---

#### `GET /metrics`
Prometheus metric scrape endpoint delivering Prometheus text format.

- **Sample Output**:
```text
# HELP crophealth_http_requests_total Total count of HTTP requests
# TYPE crophealth_http_requests_total counter
crophealth_http_requests_total{method="GET",handler="/health",status="200"} 42
crophealth_http_requests_total{method="POST",handler="/api/v1/reports/upload",status="201"} 18
# HELP crophealth_database_connected Database connection health status
# TYPE crophealth_database_connected gauge
crophealth_database_connected 1.0
```
