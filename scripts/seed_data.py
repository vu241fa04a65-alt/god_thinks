"""
CropHealthAI Database Seeding Script.
Populates initial sample users (farmers, agronomists, admin), crop scouting reports,
disease predictions, Grad-CAM overlays, expert validation actions, and leaderboard rewards.

Usage:
    python scripts/seed_data.py
    python scripts/seed_data.py --db-url postgresql://postgres:postgres@localhost:5432/crophealth_db
    python scripts/seed_data.py --db-url sqlite:///./backend/test_crophealth.db
"""

import os
import sys
import argparse
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.config import settings
from backend.app.models.entities import (
    Base,
    User,
    Report,
    DiseasePrediction,
    Reward,
    ExpertAction,
    CommunityTrend
)
from backend.app.utils.security import get_password_hash


# ---------------------------------------------------------------------------
# Seed Data Definitions
# ---------------------------------------------------------------------------

SAMPLE_USERS = [
    # Farmers
    {
        "username": "ramesh_farmer",
        "email": "ramesh@kisan.org",
        "name": "Ramesh Patel",
        "phone": "+919876543210",
        "role": "farmer",
        "points": 140,
        "preferred_language": "hi",
        "location": "Maharashtra, India",
        "location_lat": 19.0760,
        "location_lng": 72.8777,
        "geofence_radius_km": 25.0
    },
    {
        "username": "kavita_farmer",
        "email": "kavita@krishi.org",
        "name": "Kavita Rao",
        "phone": "+919876543211",
        "role": "farmer",
        "points": 110,
        "preferred_language": "te",
        "location": "Karnataka, India",
        "location_lat": 12.9716,
        "location_lng": 77.5946,
        "geofence_radius_km": 30.0
    },
    {
        "username": "suresh_farmer",
        "email": "suresh@khet.org",
        "name": "Suresh Verma",
        "phone": "+919876543212",
        "role": "farmer",
        "points": 85,
        "preferred_language": "hi",
        "location": "Punjab, India",
        "location_lat": 31.1471,
        "location_lng": 75.3412,
        "geofence_radius_km": 20.0
    },
    {
        "username": "priya_farmer",
        "email": "priya@krishi.net",
        "name": "Priya Sharma",
        "phone": "+919876543213",
        "role": "farmer",
        "points": 60,
        "preferred_language": "ta",
        "location": "Tamil Nadu, India",
        "location_lat": 11.1271,
        "location_lng": 78.6569,
        "geofence_radius_km": 25.0
    },
    # Agronomist Experts
    {
        "username": "dr_ananya",
        "email": "ananya@agronomy.ac.in",
        "name": "Dr. Ananya Sen",
        "phone": "+919876543214",
        "role": "expert",
        "points": 350,
        "preferred_language": "en",
        "location": "ICAR New Delhi",
        "location_lat": 28.6139,
        "location_lng": 77.2090,
        "geofence_radius_km": 50.0
    },
    {
        "username": "dr_mukherjee",
        "email": "rajesh@icar.gov.in",
        "name": "Dr. Rajesh Mukherjee",
        "phone": "+919876543215",
        "role": "expert",
        "points": 290,
        "preferred_language": "en",
        "location": "Kolkata, India",
        "location_lat": 22.5726,
        "location_lng": 88.3639,
        "geofence_radius_km": 50.0
    },
    # System Admin
    {
        "username": "admin_user",
        "email": "admin@crophealth.ai",
        "name": "System Administrator",
        "phone": "+919876543200",
        "role": "admin",
        "points": 500,
        "preferred_language": "en",
        "location": "CropHealthAI HQ",
        "location_lat": 12.9716,
        "location_lng": 77.5946,
        "geofence_radius_km": 100.0
    }
]

SAMPLE_REPORTS_DATA = [
    {
        "farmer_username": "ramesh_farmer",
        "crop_type": "Tomato",
        "image_path": "/storage/uploads/01_tomato_early_blight.jpg",
        "location": "Nashik, Maharashtra",
        "location_lat": 19.9975,
        "location_lng": 73.7898,
        "status": "validated",
        "notes": "Lower foliage showing dark brown target-like concentric rings.",
        "prediction": {
            "disease_name": "Tomato Early Blight",
            "confidence": 0.948,
            "overlay_path": "/storage/sample_overlays/overlay_tomato_early_blight.png",
            "explanation_text": "High activation over concentric target lesion spots on the lower leaf blade."
        },
        "expert_action": {
            "expert_username": "dr_ananya",
            "decision": "approved",
            "notes": "Classic Alternaria solani symptoms confirmed. Recommended Trichoderma bio-fungicide is optimal."
        }
    },
    {
        "farmer_username": "ramesh_farmer",
        "crop_type": "Tomato",
        "image_path": "/storage/uploads/02_tomato_late_blight.jpg",
        "location": "Pune, Maharashtra",
        "location_lat": 18.5204,
        "location_lng": 73.8567,
        "status": "pending",
        "notes": "Water-soaked dark lesions spreading rapidly after heavy monsoon drizzle.",
        "prediction": {
            "disease_name": "Tomato Late Blight",
            "confidence": 0.965,
            "overlay_path": "/storage/sample_overlays/overlay_tomato_late_blight.png",
            "explanation_text": "Strong gradient attention across large necrotic water-soaked margins."
        },
        "expert_action": None
    },
    {
        "farmer_username": "kavita_farmer",
        "crop_type": "Tomato",
        "image_path": "/storage/uploads/03_tomato_healthy.jpg",
        "location": "Mysuru, Karnataka",
        "location_lat": 12.2958,
        "location_lng": 76.6394,
        "status": "validated",
        "notes": "Routine weekly foliage checkup; no visible lesions observed.",
        "prediction": {
            "disease_name": "Tomato Healthy",
            "confidence": 0.991,
            "overlay_path": "/storage/sample_overlays/overlay_tomato_healthy.png",
            "explanation_text": "Evenly distributed background activation with zero localized necrosis detected."
        },
        "expert_action": {
            "expert_username": "dr_mukherjee",
            "decision": "approved",
            "notes": "Healthy foliage verified. Continue preventive neem oil bi-weekly schedule."
        }
    },
    {
        "farmer_username": "kavita_farmer",
        "crop_type": "Potato",
        "image_path": "/storage/uploads/04_potato_early_blight.jpg",
        "location": "Hassan, Karnataka",
        "location_lat": 13.0033,
        "location_lng": 76.1004,
        "status": "validated",
        "notes": "Early brown circular spots observed on second-tier foliage.",
        "prediction": {
            "disease_name": "Potato Early Blight",
            "confidence": 0.932,
            "overlay_path": "/storage/sample_overlays/overlay_potato_early_blight.png",
            "explanation_text": "Model identified early Alternaria necrotic spotting on interveinal tissue."
        },
        "expert_action": {
            "expert_username": "dr_ananya",
            "decision": "approved",
            "notes": "Accurate early-stage detection. Advised prompt removal of infected leaves."
        }
    },
    {
        "farmer_username": "kavita_farmer",
        "crop_type": "Potato",
        "image_path": "/storage/uploads/05_potato_late_blight.jpg",
        "location": "Belagavi, Karnataka",
        "location_lat": 15.8497,
        "location_lng": 74.4977,
        "status": "pending",
        "notes": "Extensive dark lesions accompanied by pale yellow halos.",
        "prediction": {
            "disease_name": "Potato Late Blight",
            "confidence": 0.978,
            "overlay_path": "/storage/sample_overlays/overlay_potato_late_blight.png",
            "explanation_text": "Significant neural activation highlighting Phytophthora infestans blighted zones."
        },
        "expert_action": None
    },
    {
        "farmer_username": "suresh_farmer",
        "crop_type": "Corn",
        "image_path": "/storage/uploads/06_corn_common_rust.jpg",
        "location": "Ludhiana, Punjab",
        "location_lat": 30.9010,
        "location_lng": 75.8573,
        "status": "validated",
        "notes": "Reddish-brown pustules scattered across both leaf surfaces.",
        "prediction": {
            "disease_name": "Corn Common Rust",
            "confidence": 0.954,
            "overlay_path": "/storage/sample_overlays/overlay_corn_common_rust.png",
            "explanation_text": "Dense cluster activations over Puccinia sorghi rust pustule formations."
        },
        "expert_action": {
            "expert_username": "dr_mukherjee",
            "decision": "approved",
            "notes": "Common rust confirmed. Apply bio-agent Bacillus subtilis; avoid overhead sprinklers."
        }
    },
    {
        "farmer_username": "suresh_farmer",
        "crop_type": "Corn",
        "image_path": "/storage/uploads/07_corn_northern_leaf_blight.jpg",
        "location": "Jalandhar, Punjab",
        "location_lat": 31.3260,
        "location_lng": 75.5762,
        "status": "rejected",
        "notes": "Elongated pale streaks on middle leaves.",
        "prediction": {
            "disease_name": "Corn Northern Leaf Blight",
            "confidence": 0.925,
            "overlay_path": "/storage/sample_overlays/overlay_corn_northern_blight.png",
            "explanation_text": "Broad longitudinal activations along lower leaf margins."
        },
        "expert_action": {
            "expert_username": "dr_ananya",
            "decision": "rejected",
            "notes": "Symptoms indicate severe nitrogen deficiency chlorosis rather than fungal Northern Leaf Blight."
        }
    },
    {
        "farmer_username": "priya_farmer",
        "crop_type": "Apple",
        "image_path": "/storage/uploads/08_apple_scab.jpg",
        "location": "Salem, Tamil Nadu",
        "location_lat": 11.6643,
        "location_lng": 78.1460,
        "status": "validated",
        "notes": "Olive-green to black velvety scab spots on mature foliage.",
        "prediction": {
            "disease_name": "Apple Scab",
            "confidence": 0.941,
            "overlay_path": "/storage/sample_overlays/overlay_apple_scab.png",
            "explanation_text": "Distinct activation hotspots matching Venturia inaequalis lesions."
        },
        "expert_action": {
            "expert_username": "dr_mukherjee",
            "decision": "approved",
            "notes": "Apple scab correctly diagnosed. Recommend pruning for air circulation and sulfur spray."
        }
    },
    {
        "farmer_username": "priya_farmer",
        "crop_type": "Rice",
        "image_path": "/storage/uploads/09_rice_blast.jpg",
        "location": "Thanjavur, Tamil Nadu",
        "location_lat": 10.7870,
        "location_lng": 79.1378,
        "status": "pending",
        "notes": "Spindle-shaped lesions with gray-white centers and brownish borders.",
        "prediction": {
            "disease_name": "Rice Blast",
            "confidence": 0.963,
            "overlay_path": "/storage/sample_overlays/overlay_rice_blast.png",
            "explanation_text": "High localized activation over diamond/spindle shaped Magnaporthe oryzae lesions."
        },
        "expert_action": None
    },
    {
        "farmer_username": "priya_farmer",
        "crop_type": "Wheat",
        "image_path": "/storage/uploads/10_wheat_yellow_rust.jpg",
        "location": "Madurai, Tamil Nadu",
        "location_lat": 9.9252,
        "location_lng": 78.1198,
        "status": "validated",
        "notes": "Linear stripes of yellow-orange pustules aligned with the leaf veins.",
        "prediction": {
            "disease_name": "Wheat Yellow Rust",
            "confidence": 0.957,
            "overlay_path": "/storage/sample_overlays/overlay_wheat_yellow_rust.png",
            "explanation_text": "Strong linear pattern activation following yellow stripe rust striations."
        },
        "expert_action": {
            "expert_username": "dr_ananya",
            "decision": "approved",
            "notes": "Puccinia striiformis confirmed. Advised immediate notification of neighboring wheat plots."
        }
    }
]

SAMPLE_COMMUNITY_TRENDS = [
    {
        "disease_name": "Tomato Early Blight",
        "location": "Nashik Agri Cluster, Maharashtra",
        "count": 28,
        "location_geojson": {
            "type": "Point",
            "coordinates": [73.7898, 19.9975],
            "properties": {
                "cluster_name": "Nashik Tomato Belt",
                "risk_level": "high",
                "crop": "Tomato",
                "radius_km": 25.0
            }
        }
    },
    {
        "disease_name": "Potato Late Blight",
        "location": "Belagavi Potato Region, Karnataka",
        "count": 19,
        "location_geojson": {
            "type": "Point",
            "coordinates": [74.4977, 15.8497],
            "properties": {
                "cluster_name": "Belagavi Tubers",
                "risk_level": "critical",
                "crop": "Potato",
                "radius_km": 30.0
            }
        }
    },
    {
        "disease_name": "Corn Common Rust",
        "location": "Ludhiana Plains, Punjab",
        "count": 14,
        "location_geojson": {
            "type": "Point",
            "coordinates": [75.8573, 30.9010],
            "properties": {
                "cluster_name": "Punjab Corn Corridor",
                "risk_level": "medium",
                "crop": "Corn",
                "radius_km": 20.0
            }
        }
    },
    {
        "disease_name": "Rice Blast",
        "location": "Cauvery Delta, Tamil Nadu",
        "count": 22,
        "location_geojson": {
            "type": "Point",
            "coordinates": [79.1378, 10.7870],
            "properties": {
                "cluster_name": "Thanjavur Rice Belt",
                "risk_level": "high",
                "crop": "Rice",
                "radius_km": 25.0
            }
        }
    }
]


# ---------------------------------------------------------------------------
# Seed Logic Implementation
# ---------------------------------------------------------------------------

def seed_database(db_url: str):
    """
    Connects to database, creates tables if missing, and idempotently populates
    users, reports, predictions, rewards, and community outbreak trends.
    """
    print(f"Connecting to database at: {db_url}")
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Seed Users
        print("\n--- Seeding Users (Farmers, Experts, Admin) ---")
        user_map = {}
        default_pwd_hash = get_password_hash("Password123!")

        for udata in SAMPLE_USERS:
            existing_user = session.query(User).filter(
                (User.username == udata["username"]) | (User.email == udata["email"])
            ).first()

            if existing_user:
                # Update existing user attributes idempotently
                for k, v in udata.items():
                    setattr(existing_user, k, v)
                existing_user.hashed_password = default_pwd_hash
                session.flush()
                user_map[udata["username"]] = existing_user
                print(f"Updated user: {existing_user.username} ({existing_user.role}, {existing_user.points} pts)")
            else:
                new_user = User(
                    username=udata["username"],
                    email=udata["email"],
                    name=udata["name"],
                    phone=udata["phone"],
                    role=udata["role"],
                    points=udata["points"],
                    preferred_language=udata["preferred_language"],
                    location=udata["location"],
                    location_lat=udata["location_lat"],
                    location_lng=udata["location_lng"],
                    geofence_radius_km=udata["geofence_radius_km"],
                    sms_opt_in=True,
                    hashed_password=default_pwd_hash
                )
                session.add(new_user)
                session.flush()
                user_map[udata["username"]] = new_user
                print(f"Created user: {new_user.username} ({new_user.role}, {new_user.points} pts)")

        session.commit()

        # 2. Seed Reports & Disease Predictions
        print("\n--- Seeding Crop Reports & Predictions ---")
        for rdata in SAMPLE_REPORTS_DATA:
            farmer = user_map.get(rdata["farmer_username"])
            if not farmer:
                continue

            # Idempotency check on existing report
            existing_report = session.query(Report).filter(
                Report.user_id == farmer.id,
                Report.image_path == rdata["image_path"]
            ).first()

            if not existing_report:
                existing_report = Report(
                    user_id=farmer.id,
                    crop_type=rdata["crop_type"],
                    image_path=rdata["image_path"],
                    location=rdata["location"],
                    location_lat=rdata["location_lat"],
                    location_lng=rdata["location_lng"],
                    status=rdata["status"],
                    notes=rdata["notes"]
                )
                session.add(existing_report)
                session.flush()
                print(f"Created Report #{existing_report.id} for {farmer.username} ({rdata['crop_type']})")
            else:
                existing_report.status = rdata["status"]
                existing_report.notes = rdata["notes"]
                session.flush()
                print(f"Verified Report #{existing_report.id} for {farmer.username} ({rdata['crop_type']})")

            # Seed Disease Prediction for report
            pred_data = rdata["prediction"]
            existing_pred = session.query(DiseasePrediction).filter(
                DiseasePrediction.report_id == existing_report.id,
                DiseasePrediction.disease_name == pred_data["disease_name"]
            ).first()

            if not existing_pred:
                new_pred = DiseasePrediction(
                    report_id=existing_report.id,
                    disease_name=pred_data["disease_name"],
                    confidence=pred_data["confidence"],
                    overlay_path=pred_data["overlay_path"],
                    explanation_text=pred_data["explanation_text"]
                )
                session.add(new_pred)
                session.flush()

            # Seed Expert Action if applicable
            expert_info = rdata.get("expert_action")
            if expert_info:
                expert_user = user_map.get(expert_info["expert_username"])
                if expert_user:
                    existing_action = session.query(ExpertAction).filter(
                        ExpertAction.report_id == existing_report.id,
                        ExpertAction.expert_id == expert_user.id
                    ).first()

                    if not existing_action:
                        new_action = ExpertAction(
                            report_id=existing_report.id,
                            expert_id=expert_user.id,
                            decision=expert_info["decision"],
                            notes=expert_info["notes"]
                        )
                        session.add(new_action)
                        session.flush()

        session.commit()

        # 3. Seed Reward Ledger Entries (Leaderboard History)
        print("\n--- Seeding Reward Points History ---")
        for username, user_obj in user_map.items():
            if user_obj.role != "farmer":
                continue

            existing_rewards = session.query(Reward).filter(Reward.user_id == user_obj.id).all()
            if not existing_rewards:
                # Add sample breakdown matching user's point total
                base_pts = user_obj.points
                r1 = Reward(
                    user_id=user_obj.id,
                    points=30,
                    reason="CROP_SCOUT_UPLOAD (Initial crop monitoring contribution)",
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=5)
                )
                r2 = Reward(
                    user_id=user_obj.id,
                    points=40,
                    reason="EXPERT_VERIFICATION_BONUS (Agronomist approved diagnosis)",
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=3)
                )
                rem_pts = max(0, base_pts - 70)
                r3 = Reward(
                    user_id=user_obj.id,
                    points=rem_pts,
                    reason="COMMUNITY_OUTBREAK_SURVEILLANCE (Active field alerts participation)",
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
                )
                session.add_all([r1, r2, r3])
                print(f"Created reward ledger entries for {username} (Total: {user_obj.points} pts)")

        session.commit()

        # 4. Seed Community Outbreak Trends
        print("\n--- Seeding Community Outbreak Clusters ---")
        for trend in SAMPLE_COMMUNITY_TRENDS:
            existing_trend = session.query(CommunityTrend).filter(
                CommunityTrend.disease_name == trend["disease_name"]
            ).first()

            if existing_trend:
                existing_trend.count = trend["count"]
                existing_trend.location = trend["location"]
                existing_trend.location_geojson = trend["location_geojson"]
                print(f"Updated outbreak trend: {trend['disease_name']} ({trend['count']} cases)")
            else:
                new_trend = CommunityTrend(
                    disease_name=trend["disease_name"],
                    location=trend["location"],
                    count=trend["count"],
                    location_geojson=trend["location_geojson"]
                )
                session.add(new_trend)
                print(f"Created outbreak trend: {trend['disease_name']} ({trend['count']} cases)")

        session.commit()
        print("\n============================================================")
        print(" SUCCESS: Database successfully seeded with demo dataset! ")
        print(" Default Password for all seeded users: Password123!        ")
        print("============================================================\n")

    except Exception as e:
        session.rollback()
        print(f"\nERROR: Seeding failed with exception: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed CropHealthAI sample demo dataset")
    parser.add_argument(
        "--db-url",
        "-d",
        type=str,
        default=None,
        help="Database connection URL (defaults to settings.DATABASE_URL or local sqlite)"
    )
    args = parser.parse_args()

    # Determine database URL
    db_url = args.db_url
    if not db_url:
        db_url = getattr(settings, "DATABASE_URL", None)
    if not db_url:
        db_url = "sqlite:///./backend/crophealth.db"

    # SQLite fallback relative path normalization
    if db_url.startswith("sqlite:///./"):
        rel_path = db_url.replace("sqlite:///./", "")
        abs_db_path = os.path.join(ROOT_DIR, rel_path)
        os.makedirs(os.path.dirname(abs_db_path), exist_ok=True)
        db_url = f"sqlite:///{abs_db_path.replace(os.sep, '/')}"

    seed_database(db_url)


if __name__ == "__main__":
    main()
