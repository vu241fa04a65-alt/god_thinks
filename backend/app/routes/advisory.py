import os
import csv
import yaml
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status

from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/advisory", tags=["Integrated Pest & Disease Advisory"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
PESTICIDES_CSV = os.path.join(DATA_DIR, "pesticides.csv")
RESTRICTIONS_YAML = os.path.join(CONFIG_DIR, "chemical_restrictions.yaml")

CULTURAL_PRACTICES_MAP = {
    "blight": [
        {
            "practice": "Crop Rotation",
            "description": "Rotate with non-solanaceous crops (e.g. pulses, corn, mustard) for at least 2 seasons to break pathogen lifecycle.",
            "impact": "High (reduces soil inoculum by 70%)"
        },
        {
            "practice": "Canopy Airflow Management",
            "description": "Maintain wider row spacing (minimum 60 cm x 45 cm) and prune bottom senescent leaves up to 20 cm from soil.",
            "impact": "High (lowers microclimate humidity below 80%)"
        },
        {
            "practice": "Drip Irrigation Transition",
            "description": "Avoid overhead sprinkler irrigation; deliver water directly to root zone via drip lines to prevent spore splash.",
            "impact": "Medium (prevents foliar wetness)"
        },
        {
            "practice": "Field Sanitation & Solarization",
            "description": "Collect and deeply burn or bury all diseased foliage mummies; avoid tossing culled leaves in compost.",
            "impact": "Medium (sanitizes field perimeter)"
        }
    ],
    "rust": [
        {
            "practice": "Resistant Hybrid Cultivars",
            "description": "Sow certified disease-resistant seed varieties with Yr/Sr rust resistance genes.",
            "impact": "High (primary defense)"
        },
        {
            "practice": "Regulate Nitrogen Application",
            "description": "Avoid excessive split application of urea; balanced potash (K) enhances cell wall lignification against urediniospores.",
            "impact": "Medium (reduces foliage tenderness)"
        },
        {
            "practice": "Early Morning Sowing Alignment",
            "description": "Time planting dates to avoid heading stages coinciding with peak seasonal dew formation.",
            "impact": "Medium (escapes peak infection window)"
        }
    ],
    "mildew": [
        {
            "practice": "Direct Sunlight Canopy Training",
            "description": "Trellis and prune canopy vertically to maximize direct UV exposure which degrades powdery conidia.",
            "impact": "High"
        },
        {
            "practice": "Weed Host Eradication",
            "description": "Remove wild alternate weed hosts (Chenopodium, Amaranthus) along field bunds.",
            "impact": "Medium"
        }
    ],
    "general": [
        {
            "practice": "Routine Field Scouting",
            "description": "Inspect 20 random plants across a zig-zag transect weekly; note initial focal disease patches.",
            "impact": "High (early detection prevents exponential spread)"
        },
        {
            "practice": "Straw or Plastic Mulching",
            "description": "Apply organic paddy straw mulch (5 cm layer) to block soil-borne spore splashes onto lower leaves.",
            "impact": "Medium"
        }
    ]
}


def load_pesticides_dataset() -> List[Dict[str, Any]]:
    """Load and parse pesticides from CSV file."""
    pesticides = []
    if not os.path.exists(PESTICIDES_CSV):
        logger.warning(f"Pesticides dataset file not found at: {PESTICIDES_CSV}")
        return []

    try:
        with open(PESTICIDES_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                crops = [c.strip().lower() for c in row.get("crop_applicable", "").split(",") if c.strip()]
                diseases = [d.strip().lower() for d in row.get("target_diseases", "").split(",") if d.strip()]
                eco_flag = row.get("eco_friendly_flag", "").strip().lower() in ("true", "1", "yes")

                pesticides.append({
                    "name": row.get("name", "").strip(),
                    "active_ingredient": row.get("active_ingredient", "").strip(),
                    "crops": crops,
                    "target_diseases": diseases,
                    "dosage_ml_per_liter": float(row.get("dosage_ml_per_liter", 2.0)),
                    "pre_harvest_interval_days": int(row.get("pre_harvest_interval_days", 7)),
                    "eco_friendly_flag": eco_flag,
                    "notes": row.get("notes", "").strip()
                })
    except Exception as e:
        logger.error(f"Error parsing pesticides CSV dataset: {e}")

    return pesticides


def load_regional_restrictions() -> Dict[str, Any]:
    """Load regional chemical bans and restrictions from YAML configuration."""
    if not os.path.exists(RESTRICTIONS_YAML):
        logger.warning(f"Chemical restrictions file not found at: {RESTRICTIONS_YAML}")
        return {}

    try:
        with open(RESTRICTIONS_YAML, mode="r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data
    except Exception as e:
        logger.error(f"Error reading regional restrictions YAML: {e}")
        return {}


def check_regional_status(chemical_name: str, active_ingredient: str, region: Optional[str]) -> Dict[str, Any]:
    """Check whether a chemical or active ingredient is banned or restricted in the specified region."""
    if not region:
        return {"status": "allowed", "is_banned": False, "is_restricted": False, "warning": None}

    restrictions = load_regional_restrictions()
    reg_key = region.lower().strip()
    regions_map = restrictions.get("regions", {})

    # Check for matched region
    matched_config = None
    for r_name, r_data in regions_map.items():
        if r_name in reg_key or reg_key in r_name:
            matched_config = r_data
            break

    chem_lower = chemical_name.lower()
    ai_lower = active_ingredient.lower()

    # Global ban check
    global_banned = [g.lower() for g in restrictions.get("global_banned", [])]
    for b in global_banned:
        if b in chem_lower or b in ai_lower:
            return {
                "status": "banned",
                "is_banned": True,
                "is_restricted": False,
                "warning": f"GLOBAL BAN: '{active_ingredient}' is prohibited internationally under environmental conventions."
            }

    if not matched_config:
        return {"status": "allowed", "is_banned": False, "is_restricted": False, "warning": None}

    banned_list = [b.lower() for b in matched_config.get("banned_chemicals", [])]
    restricted_list = [r.lower() for r in matched_config.get("restricted_chemicals", [])]
    reg_title = matched_config.get("name", region)

    for b in banned_list:
        if b in chem_lower or b in ai_lower:
            return {
                "status": "banned",
                "is_banned": True,
                "is_restricted": False,
                "warning": f"BANNED in {reg_title}: {matched_config.get('warning', 'Prohibited by regional agricultural authority.')}"
            }

    for r in restricted_list:
        if r in chem_lower or r in ai_lower:
            return {
                "status": "restricted",
                "is_banned": False,
                "is_restricted": True,
                "warning": f"RESTRICTED in {reg_title}: {matched_config.get('warning', 'Subject to strict regulatory limits.')}"
            }

    return {"status": "allowed", "is_banned": False, "is_restricted": False, "warning": None}


def get_cultural_practices(disease: str) -> List[Dict[str, str]]:
    """Retrieve disease-specific cultural and preventative practices."""
    disease_lower = disease.lower()
    for key, practices in CULTURAL_PRACTICES_MAP.items():
        if key in disease_lower:
            return practices
    return CULTURAL_PRACTICES_MAP["general"]


@router.get("/recommend")
def recommend_advisory(
    disease: str = Query(..., min_length=2, description="Diagnosed crop disease or pest (e.g. Early Blight, Rust)"),
    crop: str = Query(..., min_length=2, description="Host crop name (e.g. Tomato, Wheat)"),
    region: Optional[str] = Query(None, description="Geographic jurisdiction or state (e.g. Kerala, Punjab, EU)")
):
    """
    Generate ranked integrated pest and disease management (IPM) advisory:
    - Biological Controls: certified bio-pesticides & antagonist microorganisms.
    - Cultural Practices: field hygiene, spacing, and crop rotation methods.
    - Chemical Options: synthetic fungicides/pesticides with dosage, PHI, safety notes, and regional restrictions.
    - Simple Rule Engine: Prioritizes eco_friendly_flag == True options over synthetic chemicals.
    """
    norm_crop = crop.lower().strip()
    norm_disease = disease.lower().strip()

    dataset = load_pesticides_dataset()
    cultural_practices = get_cultural_practices(norm_disease)

    biological_controls = []
    chemical_options = []

    for item in dataset:
        # Match crop applicability
        crop_match = any(norm_crop in c or c in norm_crop for c in item["crops"])
        if not crop_match:
            continue

        # Match disease applicability
        disease_match = any(norm_disease in d or d in norm_disease for d in item["target_diseases"])
        if not disease_match:
            # Fallback for broad spectrum bio-agents if nothing exact matches
            if not any(token in norm_disease for token in ["blight", "rust", "rot", "mildew", "spot", "blast"]):
                continue

        reg_check = check_regional_status(item["name"], item["active_ingredient"], region)

        # Calculate Ranking Score
        # Eco-friendly base: 95; Conventional chemical base: 75
        # Shorter pre-harvest interval is safer (+bonus)
        phi_bonus = max(0, 14 - item["pre_harvest_interval_days"]) * 0.5
        base_score = 95.0 if item["eco_friendly_flag"] else 75.0
        score = base_score + phi_bonus

        # Penalize or demote restricted/banned agrochemicals
        if reg_check["is_banned"]:
            score -= 60.0
        elif reg_check["is_restricted"]:
            score -= 25.0

        option_payload = {
            "name": item["name"],
            "active_ingredient": item["active_ingredient"],
            "dosage": f"{item['dosage_ml_per_liter']} ml/L of water",
            "dosage_ml_per_liter": item["dosage_ml_per_liter"],
            "pre_harvest_interval_days": item["pre_harvest_interval_days"],
            "eco_friendly": item["eco_friendly_flag"],
            "safety_notes": item["notes"],
            "regional_status": reg_check["status"],
            "warning": reg_check["warning"],
            "rank_score": round(score, 1)
        }

        if item["eco_friendly_flag"]:
            biological_controls.append(option_payload)
        else:
            chemical_options.append(option_payload)

    # Sort each category by rank score descending
    biological_controls.sort(key=lambda x: x["rank_score"], reverse=True)
    chemical_options.sort(key=lambda x: x["rank_score"], reverse=True)

    # Create master ranked recommendations list
    # Rule engine priority order: Cultural Practices -> Eco-Friendly / Biological -> Allowed Chemicals -> Restricted
    all_ranked = []
    for bio in biological_controls:
        all_ranked.append({
            "category": "Biological / Eco-Friendly Control",
            **bio
        })
    for chem in chemical_options:
        all_ranked.append({
            "category": "Chemical Option",
            **chem
        })

    # Regional restrictions alert summary
    regional_warning = None
    if region:
        restrictions = load_regional_restrictions()
        reg_key = region.lower().strip()
        for r_name, r_data in restrictions.get("regions", {}).items():
            if r_name in reg_key or reg_key in r_name:
                regional_warning = {
                    "region": r_data.get("name", region),
                    "policy_notice": r_data.get("warning"),
                    "banned_substances": r_data.get("banned_chemicals", []),
                    "restricted_substances": r_data.get("restricted_chemicals", [])
                }
                break

    data = {
        "query": {
            "crop": crop,
            "disease": disease,
            "region": region
        },
        "summary": f"Integrated Pest Management (IPM) Advisory for {disease} in {crop}",
        "cultural_practices": cultural_practices,
        "biological_controls": biological_controls,
        "chemical_options": chemical_options,
        "all_ranked_recommendations": all_ranked,
        "regional_compliance": regional_warning
    }

    return success_envelope(data=data)
