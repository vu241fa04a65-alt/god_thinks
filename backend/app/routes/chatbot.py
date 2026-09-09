from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.entities import Report, DiseasePrediction
from backend.app.services.translation_service import translation_service
from backend.app.routes import success_envelope, error_envelope
from backend.app.utils.logger import logger

router = APIRouter(prefix="/chatbot", tags=["Chatbot & Voice Advisory"])

# Request & Response Schemas
class ChatbotAdviceRequest(BaseModel):
    message: str
    language: str = "en"  # "en", "hi", "mr", "te"
    context: Optional[Dict[str, Any]] = None  # e.g., {"report_id": 42, "crop": "Tomato"}


# Canned templates for common agricultural diseases and general farming queries
DISEASE_KNOWLEDGE_BASE = {
    "early blight": {
        "disease": "Early Blight (Alternaria solani)",
        "crops": ["Tomato", "Potato"],
        "symptoms": "Concentric rings resembling a target board with chlorotic yellow halos on lower leaves.",
        "biological": "Apply Trichoderma viride 1.5% WP (5g/liter) or cold-pressed Neem oil (3ml/liter) in evening hours.",
        "chemical": "Spray Mancozeb 75% WP (2.5g/liter) or Copper Oxychloride (3g/liter).",
        "prevention": "Prune lower infected foliage. Ensure furrow aeration and avoid overhead sprinkler watering.",
        "safety": "Observe 7-day Pre-Harvest Interval (PHI) after Mancozeb application. Wear gloves and eye protection."
    },
    "late blight": {
        "disease": "Late Blight (Phytophthora infestans)",
        "crops": ["Tomato", "Potato"],
        "symptoms": "Water-soaked dark lesions on leaf tips with white fuzzy fungal growth on leaf undersides under cool, moist conditions.",
        "biological": "Bio-formulations of Bacillus subtilis or Pseudomonas fluorescens as preventive foliar wash.",
        "chemical": "Cymoxanil 8% + Mancozeb 64% WP (2g/liter) or Metalaxyl + Mancozeb (2.5g/liter).",
        "prevention": "Destroy infected tubers and foliage immediately. Maintain wide plant spacing for rapid drying.",
        "safety": "Do not harvest within 10 days of systemic metalaxyl application. Avoid water source contamination."
    },
    "downy mildew": {
        "disease": "Downy Mildew (Plasmopara viticola)",
        "crops": ["Grape", "Cucumber", "Melon"],
        "symptoms": "Yellowish oily patches on upper leaf surface with white cottony mildew underneath.",
        "biological": "Trichoderma harzianum foliar spray at shoot elongation stage.",
        "chemical": "Bordeaux mixture (1%) or Azoxystrobin 23% SC (1ml/liter).",
        "prevention": "Canopy canopy management to permit direct sunlight and prevent leaf wetness.",
        "safety": "Toxic to aquatic life. Do not spray during windy conditions."
    },
    "rust": {
        "disease": "Common Rust (Puccinia spp.)",
        "crops": ["Corn", "Wheat"],
        "symptoms": "Golden to reddish-brown powdery pustules on both upper and lower leaf surfaces.",
        "biological": "Foliar neem seed kernel extract (NSKE 5%).",
        "chemical": "Propiconazole 25% EC (1ml/liter) or Tebuconazole.",
        "prevention": "Adopt certified rust-resistant seed cultivars and avoid excessive nitrogen fertilizer.",
        "safety": "Wear protective gear during fungicide mixing and spraying. PHI: 15 days."
    },
    "general": {
        "disease": "General Foliar Health Maintenance",
        "crops": ["Vegetables & Cereals"],
        "symptoms": "Scout fields weekly, inspecting lower leaf surfaces for spots, wilting, or pest egg clusters.",
        "biological": "Spray Panchagavya (3%) or Jeevamrutha weekly for plant vigor and systemic resistance.",
        "chemical": "Consult agricultural extension officer before applying chemical cocktails.",
        "prevention": "Practice 3-year crop rotation and deep summer plowing to eliminate overwintering spores.",
        "safety": "Always verify local chemical restrictions and banned pesticide lists."
    }
}

# Localized greetings and closures
LOCALIZED_RESPONSES = {
    "hi": {
        "intro": "नमस्ते किसान भाई! CropHealthAI सलाहकार से आपकी सहायता:",
        "disease_detected": "पहचाना गया रोग",
        "biological_control": "🌿 जैविक व सुरक्षित उपचार:",
        "chemical_control": "🧪 रासायनिक विकल्प:",
        "prevention": "🛡️ रोकथाम के उपाय:",
        "warning": "⚠️ सुरक्षा चेतावनी:",
        "fallback": "नमस्ते! कृपया अपनी फसल का नाम (जैसे टमाटर, आलू, मक्का) और लक्षण बताएं ताकि मैं सही दवा व सलाह दे सकूं।"
    },
    "mr": {
        "intro": "नमस्कार शेतकरी मित्र! CropHealthAI कडून कृषी सल्ला:",
        "disease_detected": "ओळखलेला रोग",
        "biological_control": "🌿 सेंद्रिय व जैविक उपाय:",
        "chemical_control": "🧪 रासायनिक फवारणी पर्याय:",
        "prevention": "🛡️ प्रतिबंधात्मक काळजी:",
        "warning": "⚠️ सुरक्षा सूचना:",
        "fallback": "नमस्कार! कृपया आपल्या पिकाचे नाव (उदा. टोमॅटो, बटाटा, द्राक्ष) आणि झाडावरील लक्षणे सांगा जेणेकरून अचूक फवारणी सल्ला देता येईल."
    },
    "te": {
        "intro": "నమస్కారం రైతు సోదరులారా! CropHealthAI నుండి పంట సలహా:",
        "disease_detected": "గుర్తించిన తెగులు",
        "biological_control": "🌿 సేంద్రీయ & జీవ నియంత్రణ:",
        "chemical_control": "🧪 రసాయన పిచికారీ ఎంపికలు:",
        "prevention": "🛡️ నివారణ చర్యలు:",
        "warning": "⚠️ భద్రతా హెచ్చరిక:",
        "fallback": "నమస్కారం! సరైన నివారణ కోసం మీ పంట పేరు (టమోటా, బంగాళాదుంప, మొక్కజొన్న) మరియు తెగులు లక్షణాలను తెలియజేయండి."
    },
    "en": {
        "intro": "Hello Farmer! CropHealthAI Advisory Assistant at your service:",
        "disease_detected": "Diagnosed Condition",
        "biological_control": "🌿 Biological & Eco-Friendly Controls:",
        "chemical_control": "🧪 Chemical Remedy Options:",
        "prevention": "🛡️ Preventative Cultural Practices:",
        "warning": "⚠️ Safety & Pre-Harvest Warnings:",
        "fallback": "Hello! Please mention your crop type (e.g. Tomato, Potato, Grape, Corn) and symptoms observed for targeted diagnostic advice."
    }
}


def match_disease_knowledge(query_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Matches text or context against agronomy knowledge base."""
    text = (query_text or "").lower()

    # 1. Check report context if provided
    if context and context.get("disease"):
        ctx_disease = str(context.get("disease")).lower()
        for key in DISEASE_KNOWLEDGE_BASE:
            if key in ctx_disease:
                return DISEASE_KNOWLEDGE_BASE[key]

    # 2. Check query keywords
    if any(k in text for k in ["early blight", "concentric", "rings", "target", "अगेती", "लवकर", "करपा"]):
        return DISEASE_KNOWLEDGE_BASE["early blight"]
    if any(k in text for k in ["late blight", "water soaked", "fuzzy", "पछेती", "उशिरा"]):
        return DISEASE_KNOWLEDGE_BASE["late blight"]
    if any(k in text for k in ["downy", "mildew", "oily", "केवडा", "द्राक्ष", "grape"]):
        return DISEASE_KNOWLEDGE_BASE["downy mildew"]
    if any(k in text for k in ["rust", "pustule", "रतुआ", "तांबेरा", "मक्का", "wheat"]):
        return DISEASE_KNOWLEDGE_BASE["rust"]

    # 3. Fallback to general advisory
    return DISEASE_KNOWLEDGE_BASE["general"]


@router.post("/advice")
async def get_chatbot_advice(
    payload: ChatbotAdviceRequest,
    db: Session = Depends(get_db)
):
    """
    Multilingual conversational agronomist chatbot.
    Accepts text or transcribed voice query, identifies crop disease cues,
    and returns localized step-by-step treatment and safety guidance.
    """
    user_lang = payload.language.lower() if payload.language else "en"
    if user_lang not in LOCALIZED_RESPONSES:
        user_lang = "en"

    # Context enrichment from database if report_id given
    context_data = payload.context or {}
    if context_data.get("report_id"):
        try:
            report_id = int(context_data["report_id"])
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                pred = db.query(DiseasePrediction).filter(DiseasePrediction.report_id == report.id).first()
                if pred:
                    context_data["disease"] = pred.disease_name
                context_data["crop"] = report.crop_type
        except Exception as e:
            logger.warning(f"Context lookup error for report_id: {e}")

    # 1. Translate user message to English for semantic matching if not already in English
    english_query = translation_service.translate(payload.message, target_lang="en")

    # 2. Generate rule-based / template advisory
    kb_entry = match_disease_knowledge(english_query, context_data)
    loc = LOCALIZED_RESPONSES[user_lang]

    # If greeting without specifics
    cleaned_query = english_query.strip().lower()
    if cleaned_query in ["hi", "hello", "namaste", "help", "hey", "hola"]:
        return success_envelope(data={
            "response_text": loc["fallback"],
            "language": user_lang,
            "disease": None,
            "recommended_actions": [
                "Diagnose leaf image in Report tab",
                "Check regional weather disease risk",
                "View Community outbreak map"
            ]
        })

    # Construct synthesized response text
    response_lines = [
        f"{loc['intro']}",
        f"\n📌 {loc['disease_detected']}: {kb_entry['disease']}",
        f"🌾 Applicable Crops: {', '.join(kb_entry['crops'])}",
        f"\n{loc['biological_control']}\n• {kb_entry['biological']}",
        f"\n{loc['chemical_control']}\n• {kb_entry['chemical']}",
        f"\n{loc['prevention']}\n• {kb_entry['prevention']}",
        f"\n{loc['warning']}\n• {kb_entry['safety']}"
    ]
    full_english_response = "\n".join(response_lines)

    # 3. If target language is non-English, translate parts through translation service
    if user_lang != "en":
        final_text = (
            f"{loc['intro']}\n\n"
            f"📌 {loc['disease_detected']}: {translation_service.translate(kb_entry['disease'], user_lang)}\n\n"
            f"{loc['biological_control']}\n• {translation_service.translate(kb_entry['biological'], user_lang)}\n\n"
            f"{loc['chemical_control']}\n• {translation_service.translate(kb_entry['chemical'], user_lang)}\n\n"
            f"{loc['prevention']}\n• {translation_service.translate(kb_entry['prevention'], user_lang)}\n\n"
            f"{loc['warning']}\n• {translation_service.translate(kb_entry['safety'], user_lang)}"
        )
    else:
        final_text = full_english_response

    # Recommended action items
    actions = [
        f"Apply {kb_entry['crops'][0]} bio-fungicide in the evening",
        "Inspect leaf undersides for concentric lesions",
        "Avoid overhead sprinkler irrigation"
    ]

    return success_envelope(data={
        "response_text": final_text,
        "disease_matched": kb_entry["disease"],
        "language": user_lang,
        "recommended_actions": actions,
        "safety_warning": kb_entry["safety"],
        "context_applied": context_data
    })
