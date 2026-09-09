import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CropHealthAI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Security / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "crophealth-super-secret-key-change-in-production-32b")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database (PostgreSQL with graceful fallback)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/crophealth_db")

    # Third Party Integrations
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    GOOGLE_TRANSLATE_API_KEY: str = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ML_INFERENCE_ENDPOINT: str = os.getenv("ML_INFERENCE_ENDPOINT", "http://localhost:8000/ml/inference")
    ML_RUN_LOCAL: bool = os.getenv("ML_RUN_LOCAL", "true").lower() in ("true", "1", "yes")
    INTERNAL_ML_ENDPOINT: str = os.getenv("INTERNAL_ML_ENDPOINT", "http://127.0.0.1:8000/ml/infer")

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
