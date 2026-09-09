from backend.app.utils.logger import logger

LANGUAGE_DICT = {
    "hi": {
        "Healthy": "स्वस्थ",
        "Tomato Early Blight": "टमाटर का अगेती झुलसा",
        "Tomato Late Blight": "टमाटर का पछेती झुलसा",
        "Potato Early Blight": "आलू का अगेती झुलसा",
        "Apple Scab": "सेब का पपड़ी रोग",
        "Corn Common Rust": "मक्के का रतुआ रोग",
        "Moderate": "मध्यम",
        "Severe": "गंभीर",
        "Low": "कम"
    },
    "te": {
        "Healthy": "ఆరోగ్యకరమైనది",
        "Tomato Early Blight": "టమోటా ముందస్తు తెగులు",
        "Tomato Late Blight": "టమోటా ఆలస్యపు తెగులు",
        "Moderate": "మధ్యస్థం",
        "Severe": "తీవ్రమైనది",
        "Low": "తక్కువ"
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
    def translate(self, text: str, target_lang: str = "en") -> str:
        if not text or target_lang == "en":
            return text
        lang_map = LANGUAGE_DICT.get(target_lang, {})
        return lang_map.get(text, f"[{target_lang.upper()}] {text}")

translation_service = TranslationService()
