# CropHealthAI API Specification (v1.0.0)

Welcome to the **CropHealthAI RESTful API** documentation. CropHealthAI provides state-of-the-art machine learning disease diagnosis, Grad-CAM explainability, weather risk assessment, expert verification workflows, gamified community reporting, integrated pest management (IPM) advisories, and offline synchronization for low-connectivity agriculture field scouting.

---

## 1. General API Conventions

### Base URL & Versioning
All current API endpoints are prefixed with `/api/v1` for version control:
- **Base URL**: `https://api.crophealthai.com/api/v1` (or `http://localhost:8000/api/v1` in local development)
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`
- OpenAPI JSON Spec: `http://localhost:8000/api/v1/openapi.json`

### Authentication & Authorization
CropHealthAI uses JSON Web Tokens (JWT) for authentication.
- Format: `Authorization: Bearer <ACCESS_TOKEN>`
- Tokens are obtained via `POST /api/v1/auth/login`.
- Tokens expire in 60 minutes (`refresh_token` valid for 7 days).
- **Roles**:
  - `farmer` / `user`: Standard field access (reporting, community, advisory, rewards).
  - `expert`: Agronomist role required to approve/reject predictions (`@require_role("expert")`).
  - `admin`: Full administrative access.

### Standard Rate Limit Headers
Every response includes real-time rate limit headers:
```http
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 300
```
- For failed login attempts or abuse, HTTP status `429 Too Many Requests` is returned once the limit is exceeded.

### Standard Envelope Format
All responses strictly conform to the standardized JSON envelope:

#### Success Response
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

#### Error Response
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Human-readable explanation of error",
    "code": 404,
    "details": null
  }
}
```

### Common HTTP Status Codes
| Code | Meaning | Description |
| :--- | :--- | :--- |
| `200 OK` | Success | Request succeeded. |
| `201 Created` | Resource Created | Resource successfully created (e.g. registration, report upload). |
| `400 Bad Request` | Client Error | Invalid input or business logic constraint violation. |
| `401 Unauthorized` | Auth Required | Missing, expired, or invalid JWT token. |
| `403 Forbidden` | Access Denied | Insufficient permissions (e.g. non-expert attempting validation). |
| `404 Not Found` | Not Found | Target resource does not exist. |
| `422 Unprocessable Entity` | Schema Validation | Pydantic validation failure. |
| `429 Too Many Requests` | Rate Limited | Rate limit exceeded. Try again after reset period. |
| `500 Internal Server Error` | Server Error | Unhandled backend exception. |

---

## 2. API Endpoint Directory

| Tag | Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/register` | Register new farmer or expert account | No |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate credentials & retrieve JWT pair | No |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Refresh access token using refresh token | No |
| **Auth** | `POST` | `/api/v1/auth/logout` | Invalidate current session | Yes |
| **Reports** | `POST` | `/api/v1/reports/upload` | Upload crop leaf image & initiate diagnosis | Optional |
| **Reports** | `GET` | `/api/v1/reports/` | List submitted scouting reports | Optional |
| **Reports** | `GET` | `/api/v1/reports/{id}` | Fetch detailed scouting report & overlay | Optional |
| **Expert** | `GET` | `/api/v1/expert/pending` | Fetch pending predictions awaiting review | Yes (`expert`) |
| **Expert** | `POST` | `/api/v1/expert/validate` | Approve or reject a model prediction | Yes (`expert`) |
| **Expert** | `GET` | `/api/v1/expert/audit-trail` | Audit log of expert decisions | Yes (`expert`) |
| **Community** | `POST` | `/api/v1/community/report` | Lightweight community disease reporting | Optional |
| **Community** | `GET` | `/api/v1/community/trends` | GeoJSON cluster aggregation of disease outbreaks | No |
| **Community** | `GET` | `/api/v1/community/nearby` | Query active reports within radius | No |
| **Gamification** | `GET` | `/api/v1/gamification/points` | View authenticated user points & history | Yes |
| **Gamification** | `GET` | `/api/v1/gamification/leaderboard`| Top ranked farmers by contributions | No |
| **Gamification** | `GET` | `/api/v1/gamification/catalog` | List redeemable farming reward badges & vouchers| No |
| **Gamification** | `POST` | `/api/v1/gamification/claim` | Redeem points for farming reward items | Yes |
| **Weather Risk** | `GET` | `/api/v1/weather/risk` | 3-day weather risk score & preventive actions | No |
| **Advisory** | `GET` | `/api/v1/advisory/recommend` | Ranked bio & eco-friendly pest advisory | No |
| **Advisory** | `GET` | `/api/v1/advisory/restrictions`| Regional banned/restricted pesticide registry | No |
| **Alerts** | `POST` | `/api/v1/alerts/sms` | Broadcast geo-fenced outbreak SMS alerts | Yes (`expert`/`admin`) |
| **Sync** | `POST` | `/api/v1/sync/batch` | Offline report batch synchronization | Optional |
| **Sync** | `GET` | `/api/v1/sync/device-status/{id}` | Check device sync state and record counts | No |
| **ML Inference** | `POST` | `/api/v1/ml/infer` | Direct explainability inference (Grad-CAM) | No |
| **Health** | `GET` | `/api/v1/health` | Service uptime and dependencies check | No |

---

## 3. Detailed Endpoint Documentation & Examples

### 3.1 Authentication

#### `POST /api/v1/auth/register`
Create a new user account with phone and email uniqueness validation.
- **Request Body**:
```json
{
  "email": "farmer.ramesh@agri.in",
  "phone": "+919876543210",
  "name": "Ramesh Kumar",
  "password": "SecurePassword123!",
  "role": "farmer"
}
```
- **Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "farmer.ramesh@agri.in",
    "phone": "+919876543210",
    "name": "Ramesh Kumar",
    "role": "farmer",
    "points": 0,
    "created_at": "2026-09-09T08:00:00Z"
  },
  "error": null
}
```

#### `POST /api/v1/auth/login`
Authenticate using email and password. Protected by brute-force rate limiter.
- **Request Body**:
```json
{
  "email": "farmer.ramesh@agri.in",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "email": "farmer.ramesh@agri.in",
      "name": "Ramesh Kumar",
      "role": "farmer",
      "points": 0
    }
  },
  "error": null
}
```

---

### 3.2 Crop Leaf Reports & Diagnosis

#### `POST /api/v1/reports/upload`
Upload leaf photo (JPEG, PNG, WebP) with multipart form data. Automatically generates high-res storage, web thumbnail, runs ML inference, and computes Grad-CAM overlay heatmap.
- **Form Data**:
  - `file`: image binary file.
  - `crop_type`: string (e.g. `Tomato`)
  - `location`: string (e.g. `Nashik, Maharashtra`)
  - `latitude`: float (e.g. `19.9975`)
  - `longitude`: float (e.g. `73.7898`)
  - `notes`: string (optional)
- **Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "report_id": 42,
    "crop_type": "Tomato",
    "disease_predicted": "Tomato Early Blight",
    "confidence": 0.942,
    "status": "pending_expert_review",
    "image_url": "/storage/uploads/img_42.jpg",
    "thumbnail_url": "/storage/uploads/img_42_thumb.jpg",
    "overlay_url": "/storage/overlays/overlay_img_42.png",
    "explanation": {
      "visual_cues": "Concentric rings with chlorotic margin detected on leaf tissue",
      "infected_boxes": [
        {"x_min": 120, "y_min": 145, "x_max": 280, "y_max": 310, "confidence": 0.94}
      ]
    },
    "created_at": "2026-09-09T08:15:00Z"
  },
  "error": null
}
```

---

### 3.3 Expert Agronomist Workflow

#### `POST /api/v1/expert/validate`
Agronomist review endpoint. Requires `expert` role JWT.
- **Headers**:
  - `Authorization: Bearer <EXPERT_JWT>`
- **Request Body**:
```json
{
  "report_id": 42,
  "decision": "approve",
  "notes": "Verified Alternaria solani symptoms. Recommended copper fungicide spray."
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "report_id": 42,
    "status": "validated",
    "reviewed_by_expert_id": 2,
    "reviewed_at": "2026-09-09T08:30:00Z",
    "points_awarded": 5,
    "notes": "Verified Alternaria solani symptoms. Recommended copper fungicide spray."
  },
  "error": null
}
```

---

### 3.4 Community Surveillance & GeoJSON Trends

#### `GET /api/v1/community/trends?bbox=73.5,19.5,74.5,20.5&disease=Early%20Blight&since=2026-09-01`
Fetches outbreak clusters in GeoJSON format, cached via Redis/in-memory LRU.
- **Query Parameters**:
  - `bbox`: `min_lon,min_lat,max_lon,max_lat`
  - `disease`: filter by disease name
  - `since`: ISO date string
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
          "coordinates": [73.7898, 19.9975]
        },
        "properties": {
          "village": "Nashik Rural",
          "disease": "Tomato Early Blight",
          "crop": "Tomato",
          "case_count": 14,
          "severity": "high",
          "last_detected": "2026-09-09T08:15:00Z"
        }
      }
    ],
    "total_cases": 14,
    "cached": true
  },
  "error": null
}
```

---

### 3.5 Weather Risk Microservice

#### `GET /api/v1/weather/risk?lat=19.9975&lng=73.7898&crop=Tomato`
Evaluates hyper-local 3-day weather forecast against disease susceptibility matrix (`crop_rules.yaml`).
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "crop": "Tomato",
    "location": {"latitude": 19.9975, "longitude": 73.7898},
    "risk_score": 78,
    "risk_level": "High",
    "risk_reasons": [
      "High relative humidity (88%) exceeding 80% threshold",
      "Persistent leaf wetness window with temperatures at 24°C favorable for fungal sporulation",
      "Rainfall probability > 70% in next 48 hours"
    ],
    "preventive_actions": [
      "Ensure proper furrow drainage to prevent waterlogging around root zone",
      "Apply protective copper oxychloride or bio-fungicide before rainfall event",
      "Avoid overhead sprinkler irrigation"
    ],
    "forecast_days": 3
  },
  "error": null
}
```

---

### 3.6 Integrated Pest Advisory

#### `GET /api/v1/advisory/recommend?crop=Tomato&disease=Early%20Blight&region=Maharashtra`
Returns ranked remedies prioritizing eco-friendly biological controls and checking regional chemical bans (`chemical_restrictions.yaml`).
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "crop": "Tomato",
    "disease": "Early Blight",
    "region": "Maharashtra",
    "recommendations": [
      {
        "category": "Biological & Eco-friendly",
        "name": "Trichoderma viride",
        "active_ingredient": "Trichoderma viride 1.5% WP",
        "dosage": "5g per liter of water",
        "phi_days": 0,
        "eco_friendly": true,
        "instructions": "Foliar spray in the evening; repeat after 10 days"
      },
      {
        "category": "Chemical",
        "name": "Mancozeb 75% WP",
        "active_ingredient": "Mancozeb",
        "dosage": "2.5g per liter of water",
        "phi_days": 7,
        "eco_friendly": false,
        "instructions": "Apply at first onset of spots; ensure full coverage"
      }
    ],
    "warnings": []
  },
  "error": null
}
```

---

### 3.7 Offline Sync Endpoint

#### `POST /api/v1/sync/batch`
Synchronizes reports accumulated offline on mobile devices or edge hubs.
- **Request Body**:
```json
{
  "device_id": "TAB-FIELD-004",
  "reports": [
    {
      "local_id": "offline_rep_101",
      "crop_type": "Wheat",
      "symptoms": "Yellow stripe lesions on leaves",
      "latitude": 30.7333,
      "longitude": 76.7794,
      "captured_at": "2026-09-09T07:10:00Z"
    }
  ]
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "device_id": "TAB-FIELD-004",
    "processed_count": 1,
    "synced_records": [
      {"local_id": "offline_rep_101", "server_id": 98, "status": "recorded"}
    ],
    "synced_at": "2026-09-09T08:35:00Z"
  },
  "error": null
}
```

---

## 4. Key Workflows & Sample cURL Commands

### Flow 1: Farmer Image Upload & Explainable Diagnosis
Uploads a suspected infected leaf image to obtain instant predictions and Grad-CAM visual heatmaps.

```bash
curl -X POST "http://localhost:8000/api/v1/reports/upload" \
  -H "Accept: application/json" \
  -F "crop_type=Tomato" \
  -F "location=Nashik Rural" \
  -F "latitude=19.9975" \
  -F "longitude=73.7898" \
  -F "notes=Spots appearing after monsoon showers" \
  -F "file=@/path/to/sample_leaf.jpg;type=image/jpeg"
```

---

### Flow 2: Expert Agronomist Validation
Agronomist logs in, inspects pending records, and validates or rejects the AI model output.

```bash
# Step 1: Login as Expert to obtain JWT
EXPERT_TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.rao@agri.gov.in",
    "password": "ExpertSecretPassword123!"
  }' | jq -r '.data.access_token')

# Step 2: Fetch Pending Submissions
curl -s -X GET "http://localhost:8000/api/v1/expert/pending?limit=10" \
  -H "Authorization: Bearer $EXPERT_TOKEN"

# Step 3: Approve and Validate Report
curl -X POST "http://localhost:8000/api/v1/expert/validate" \
  -H "Authorization: Bearer $EXPERT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 42,
    "decision": "approve",
    "notes": "Verified Alternaria solani. Standard Mancozeb / Trichoderma treatment recommended."
  }'
```

---

### Flow 3: Community Outbreak Trends Query (GeoJSON)
Fetches aggregated outbreak locations and cluster counts within a geographical bounding box.

```bash
curl -X GET "http://localhost:8000/api/v1/community/trends?bbox=73.0,19.0,75.0,21.0&disease=Tomato%20Early%20Blight&since=2026-09-01" \
  -H "Accept: application/json"
```

---

### Flow 4: Hyper-local Weather Disease Risk Forecast
Queries micro-climate risk score and preventive farming advisories based on 3-day meteorological forecast.

```bash
curl -X GET "http://localhost:8000/api/v1/weather/risk?lat=19.9975&lng=73.7898&crop=Tomato" \
  -H "Accept: application/json"
```

---

### Flow 5: Field Scout Offline Sync
Batch uploads offline scouting records collected in network-deprived fields.

```bash
curl -X POST "http://localhost:8000/api/v1/sync/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "FIELD-SCOUT-NORTH-01",
    "reports": [
      {
        "local_id": "local_101",
        "crop_type": "Potato",
        "symptoms": "Dark water-soaked lesions on lower foliage",
        "latitude": 27.1767,
        "longitude": 78.0081,
        "captured_at": "2026-09-09T06:30:00Z"
      },
      {
        "local_id": "local_102",
        "crop_type": "Potato",
        "symptoms": "Tubers showing superficial dry rot",
        "latitude": 27.1800,
        "longitude": 78.0120,
        "captured_at": "2026-09-09T07:15:00Z"
      }
    ]
  }'
```
