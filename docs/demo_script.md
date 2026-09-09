# CropHealthAI - Live Hackathon Demo Script 🌾

This document provides a comprehensive, step-by-step presentation and live demo script tailored for hackathons, investor pitches, and judge evaluations. It showcases the complete loop: from farmer field scouting and AI diagnosis to community surveillance and agronomist verification.

---

## 🎬 Demo Overview & Timing

| Act | Scene | Duration | Key Feature Highlighted |
| :--- | :--- | :--- | :--- |
| **Act 1** | Farmer Onboarding & Authentication | 1.0 min | Role-based JWT auth, secure cookies, fast UX |
| **Act 2** | Diseased Leaf Upload & Diagnosis | 1.5 min | Vision AI classifier, malware scanning, fast inference |
| **Act 3** | Explainability & Multilingual IPM | 2.0 min | Grad-CAM lesion heatmap, localized vernacular advisory |
| **Act 4** | Outbreak Hotspot & Leaderboard | 1.5 min | GeoJSON clustering, gamification points, badges |
| **Act 5** | Agronomist Expert Review Loop | 2.0 min | Expert portal, audit logging, bonus points award |
| **Total** | | **8.0 min** | **End-to-End Precision Agriculture Platform** |

---

## 🛠️ Pre-Demo Checklist & Setup

1. **Start Backend & Frontend Services**:
   ```bash
   # Terminal 1: Backend API
   cd backend
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

   # Terminal 2: Frontend Web App
   cd frontend
   npm run dev -- --host
   ```
2. **Open Browser Tabs**:
   - Tab 1: Frontend Application (`http://localhost:5173`)
   - Tab 2: Backend Swagger UI (`http://localhost:8000/docs`)
   - Tab 3: Prometheus Metrics (`http://localhost:8000/metrics`)
3. **Sample Test Image**:
   - Ensure a sample tomato blight image is ready (e.g. `tests/sample_images/tomato_early_blight.jpg` or any leaf image).

---

## Act 1: Farmer Login & Profile Setup

### 🗣️ Presenter Talking Points
> *"In rural farming communities, access to timely agricultural expertise is scarce. Let's start with Farmer Ramesh in Maharashtra, India. Ramesh accesses CropHealthAI on his mobile browser. His session is protected by enterprise-grade security headers, rate limiting, and HttpOnly authentication cookies."*

### 💻 Step 1.1: Authenticate as Farmer Ramesh

#### API Command (cURL):
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ramesh_farmer",
    "password": "FarmerPassword123!"
  }' \
  -c farmer_cookies.txt
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 10,
      "name": "Ramesh Patel",
      "username": "ramesh_farmer",
      "email": "ramesh@kisan.org",
      "phone": "+919876543210",
      "role": "farmer",
      "points": 50
    }
  },
  "error": null
}
```

> **UI Screenshot Placeholder**:
> ![Farmer Login & Dashboard View](./screenshots/01_farmer_login.png)
> *(Shows farmer dashboard greeting "Welcome Ramesh", current balance of 50 points, and active subscription to Hindi SMS alerts).*

---

## Act 2: Upload Diseased Leaf Image

### 🗣️ Presenter Talking Points
> *"Walking through his tomato crop this morning, Ramesh spots brown concentric lesions on the lower leaves. Instead of waiting days for an extension worker, he snaps a photo and submits it. CropHealthAI instantly sanitizes the upload, verifies binary magic bytes against malicious payloads, compresses a fast thumbnail, and feeds the image to our convolutional neural network."*

### 💻 Step 2.1: Submit Crop Leaf Image for AI Diagnosis

#### API Command (cURL):
```bash
curl -X POST "http://localhost:8000/api/v1/reports/upload" \
  -H "Authorization: Bearer <FARMER_ACCESS_TOKEN>" \
  -F "file=@sample_tomato_blight.jpg" \
  -F "crop_type=Tomato" \
  -F "latitude=19.0760" \
  -F "longitude=72.8777" \
  -F "language=hi"
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "id": 104,
    "crop_type": "Tomato",
    "disease_name": "Tomato Early Blight",
    "confidence": 0.948,
    "severity": "High",
    "status": "pending",
    "image_url": "/storage/uploads/img_1725892100_7c2b4e.jpg",
    "thumbnail_url": "/storage/thumbnails/img_1725892100_7c2b4e_thumb.jpg",
    "overlay_url": "/storage/overlays/img_1725892100_7c2b4e_gradcam.jpg",
    "location": "19.0760, 72.8777",
    "points_awarded": 10,
    "created_at": "2026-09-09T18:45:10Z"
  },
  "error": null
}
```

> **UI Screenshot Placeholder**:
> ![Leaf Upload & Diagnostic Scanner](./screenshots/02_leaf_upload.png)
> *(Shows upload card with drag-and-drop zone, camera capture button, upload progress bar, and instant +10 point confetti animation).*

---

## Act 3: Explainable AI, Grad-CAM Overlay & Localized Advisory

### 🗣️ Presenter Talking Points
> *"Black-box AI isn't trusted by farmers or agronomists. That is why CropHealthAI generates Grad-CAM attention heatmaps: the bright yellow-red areas show exactly where the neural network found fungal concentric rings. Furthermore, our IPM engine checks regional chemical bans and translates organic remedies into Ramesh's local dialect (Hindi)."*

### 💻 Step 3.1: Retrieve Diagnostic Report with Grad-CAM & Localized Advisory

#### API Command (cURL):
```bash
curl -X GET "http://localhost:8000/api/v1/advisory/recommend?disease=Tomato+Early+Blight&crop=Tomato&region=maharashtra&language=hi"
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "crop": "Tomato",
    "disease": "Tomato Early Blight",
    "language": "hi",
    "recommendations": [
      {
        "name": "ट्राइकोडर्मा विरिडी (Trichoderma viride)",
        "category": "Biological Fungicide",
        "eco_friendly": true,
        "dosage": "5 ग्राम प्रति लीटर पानी",
        "pre_harvest_interval_days": 1,
        "safety_notes": "पर्यावरण और मधुमक्खियों के लिए सुरक्षित। कटाई से 24 घंटे पहले तक प्रयोग किया जा सकता है।"
      },
      {
        "name": "कॉपर ऑक्सीक्लोराइड (Copper Oxychloride 50% WP)",
        "category": "Inorganic Protective",
        "eco_friendly": false,
        "dosage": "2.5 ग्राम प्रति लीटर पानी",
        "pre_harvest_interval_days": 7,
        "safety_notes": "सुरक्षा मास्क पहनें। कटाई से कम से कम 7 दिन पहले छिड़काव बंद करें।"
      }
    ]
  },
  "error": null
}
```

> **UI Screenshot Placeholder**:
> ![Grad-CAM Overlay & Bilingual Advisory Card](./screenshots/03_diagnosis_advisory.png)
> *(Shows toggleable side-by-side: original leaf image vs. Grad-CAM visual heatmap overlay, confidence gauge at 94.8%, green "Eco-Friendly / Bio" badge, and 7-day Pre-Harvest Interval warning).*

---

## Act 4: Outbreak Hotspot Map & Leaderboard Updates

### 🗣️ Presenter Talking Points
> *"Individual diagnoses feed directly into community biosecurity. Notice how Ramesh's submission immediately populates on the regional surveillance map. Other farmers within 25 kilometers are alerted before the fungal spores spread. Plus, Ramesh's points balance climbed to 60, elevating him on the regional leaderboard!"*

### 💻 Step 4.1: Query Regional Outbreak Clusters (GeoJSON)

#### API Command (cURL):
```bash
curl -X GET "http://localhost:8000/api/v1/community/trends?crop_type=Tomato&days=7"
```

#### Expected JSON Output:
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
          "cluster_id": "cluster_mh_04",
          "crop_type": "Tomato",
          "dominant_disease": "Tomato Early Blight",
          "case_count": 8,
          "risk_level": "high",
          "radius_km": 25.0,
          "last_detected": "2026-09-09T18:45:10Z"
        }
      }
    ]
  },
  "error": null
}
```

### 💻 Step 4.2: Inspect Community Leaderboard

#### API Command (cURL):
```bash
curl -X GET "http://localhost:8000/api/v1/gamification/leaderboard?limit=5"
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "region": "Maharashtra Agri Zone",
    "rankings": [
      {
        "rank": 1,
        "name": "Kavita Rao",
        "points": 120,
        "badge": "Master Agronomist"
      },
      {
        "rank": 2,
        "name": "Ramesh Patel",
        "points": 60,
        "badge": "Silver Scout"
      }
    ]
  },
  "error": null
}
```

> **UI Screenshot Placeholder**:
> ![Outbreak Heatmap & Community Leaderboard](./screenshots/04_hotspot_leaderboard.png)
> *(Shows interactive Leaflet map with pulsing orange/red outbreak cluster circle around coordinates and leaderboard card highlighting Ramesh climbing to Rank #2 with 'Silver Scout' badge).*

---

## Act 5: Expert Validation Portal & Point Awarding

### 🗣️ Presenter Talking Points
> *"To ensure 100% data integrity, CropHealthAI includes an agronomist review portal. Here, Dr. Ananya Sen logs in with her expert credentials. She inspects Ramesh's report, verifies the concentric fungal lesions, and clicks 'Approve'. An immutable audit trail is logged, and Ramesh automatically receives a +20 point verification bonus!"*

### 💻 Step 5.1: Login as Expert Agronomist Dr. Ananya Sen

#### API Command (cURL):
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_ananya",
    "password": "ExpertPassword123!"
  }'
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 2,
      "name": "Dr. Ananya Sen",
      "username": "dr_ananya",
      "role": "expert"
    }
  },
  "error": null
}
```

---

### 💻 Step 5.2: Expert Approves Report & Records Notes

#### API Command (cURL):
```bash
curl -X POST "http://localhost:8000/api/v1/expert/validate" \
  -H "Authorization: Bearer <EXPERT_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 104,
    "status": "approved",
    "expert_notes": "Confirmed Alternaria solani (Early Blight). Recommended Trichoderma bio-fungicide is optimal."
  }'
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "report_id": 104,
    "status": "approved",
    "expert_id": 2,
    "bonus_points_awarded": 20,
    "audit_trail_id": 981,
    "message": "Report successfully validated and points awarded to farmer."
  },
  "error": null
}
```

---

### 💻 Step 5.3: Verify Farmer's New Points Balance (+20 Bonus)

#### API Command (cURL):
```bash
curl -X GET "http://localhost:8000/api/v1/gamification/points" \
  -H "Authorization: Bearer <FARMER_ACCESS_TOKEN>"
```

#### Expected JSON Output:
```json
{
  "success": true,
  "data": {
    "total_points": 80,
    "level": "Silver Scout",
    "badges": [
      { "id": "expert_verified", "name": "Expert Verified", "icon": "🏅" }
    ],
    "history": [
      { "action": "CROP_SCOUT_UPLOAD", "points": 10, "created_at": "2026-09-09T18:45:10Z" },
      { "action": "EXPERT_VERIFICATION_BONUS", "points": 20, "created_at": "2026-09-09T18:48:30Z" }
    ]
  },
  "error": null
}
```

> **UI Screenshot Placeholder**:
> ![Expert Portal & Verification Toast](./screenshots/05_expert_approval.png)
> *(Shows Expert Review table, side-by-side zoom of leaf lesion, 'Approve' modal with agronomist signature, and live notification toast: "Report #104 verified. +20 Points credited to Ramesh").*

---

## 🎯 Wrap-Up & Judge Talking Points

1. **Autonomous Yet Accountable**: Computer vision diagnoses leaf diseases in under 500ms, while expert-in-the-loop ensures grounded scientific validation.
2. **Explainable AI (XAI)**: Grad-CAM heatmap overlays build trust with farmers who can see why the model reached its decision.
3. **Multilingual & Eco-Friendly First**: Advisories prioritize bio-fungicides and respect regional chemical restrictions, delivered in local languages.
4. **Community Biosecurity**: Geo-fenced SMS outbreak warnings protect neighboring farmers before blights spread uncontrollably.
5. **Hardened & Observable**: HTTPS, HSTS, secure cookies, sliding-window rate limiters, Prometheus metrics, and automated GitHub CI/CD make CropHealthAI production-ready today.
