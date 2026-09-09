from functools import lru_cache
from typing import Dict
from backend.app.config import settings
from backend.app.utils.logger import logger

LANGUAGE_DICT: Dict[str, Dict[str, str]] = {
    "hi": {
        "Healthy": "स्वस्थ",
        "Tomato Early Blight": "टमाटर का अगेती झुलसा",
        "Tomato Late Blight": "टमाटर का पछेती झुलसा",
        "Potato Early Blight": "आलू का अगेती झुलसा",
        "Apple Scab": "सेब का पपड़ी रोग",
        "Corn Common Rust": "मक्के का रतुआ रोग",
        "Moderate": "मध्यम",
        "Severe": "गंभीर",
        "Low": "कम",
        "Treatment Advisory": "उपचार परामर्श",
        "Preventive Actions": "निवारक उपाय",
        "Safety Warning": "सुरक्षा चेतावनी",
        "Recommended Chemicals": "अनुशंसित रसायन",
        "Biological Control": "जैविक नियंत्रण"
    },
    "mr": {
        "Healthy": "निरोगी",
        "Tomato Early Blight": "टोमॅटोवरील लवकर येणारा करपा",
        "Tomato Late Blight": "टोमॅटोवरील उशिरा येणारा करपा",
        "Potato Early Blight": "बटाट्यावरील लवकर येणारा करपा",
        "Grape Downy Mildew": "द्राक्षावरील केवडा रोग",
        "Moderate": "मध्यम",
        "Severe": "तीव्र",
        "Low": "कमी",
        "Treatment Advisory": "उपचार सल्ला",
        "Preventive Actions": "प्रतिबंधात्मक उपाय",
        "Safety Warning": "सुरक्षा चेतावणी",
        "Recommended Chemicals": "शिफारस केलेली रसायने",
        "Biological Control": "जैविक नियंत्रण"
    },
    "te": {
        "Healthy": "ఆరోగ్యకరమైనది",
        "Tomato Early Blight": "టమోటా ముందస్తు తెగులు",
        "Tomato Late Blight": "టమోటా ఆలస్యపు తెగులు",
        "Moderate": "మధ్యస్థం",
        "Severe": "తీవ్రమైనది",
        "Low": "తక్కువ",
        "Treatment Advisory": "చికిత్స సలహా",
        "Preventive Actions": "నివారణ చర్యలు",
        "Safety Warning": "భద్రతా హెచ్చరిక",
        "Recommended Chemicals": "సిఫార్సు చేయబడిన రసాయనాలు",
        "Biological Control": "జీవ నియంత్రణ"
    },
    "ta": {
        "Healthy": "ஆரோக்கியமானது",
        "Tomato Early Blight": "தக்காளி ஆரம்பக்கால கருகல்",
        "Moderate": "மிதமான",
        "Severe": "கடுமையான",
        "Low": "குறைவான"
    }
}

class TranslationService:
    def __init__(self):
        self.api_key = settings.GOOGLE_TRANSLATE_API_KEY
        self.client = None
        self._cache: Dict[str, str] = {}

        if self.api_key:
            try:
                from google.cloud import translate_v2 as translate
                self.client = translate.Client()
                logger.info("Google Cloud Translate client initialized.")
            except Exception as e:
                logger.warning(f"Google Cloud Translate initialization note: {e}")

    @lru_cache(maxsize=1024)
    def translate(self, text: str, target_lang: str = "en") -> str:
        """Translate text to target language with LRU caching."""
        if not text or target_lang == "en":
            return text

        cache_key = f"{target_lang}:{text}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Google Cloud Translate client if available
        if self.client:
            try:
                result = self.client.translate(text, target_language=target_lang)
                translated = result.get("translatedText", text)
                self._cache[cache_key] = translated
                return translated
            except Exception as e:
                logger.error(f"Google Translate API call failed: {e}")

        # 2. Curated dictionary fallback
        lang_map = LANGUAGE_DICT.get(target_lang, {})
        translated = lang_map.get(text, f"[{target_lang.upper()}] {text}")
        self._cache[cache_key] = translated
        return translated

translation_service = TranslationService()
