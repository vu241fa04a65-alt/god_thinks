import os
from typing import Optional
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

    # Cloud Storage / AWS S3
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME", "")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    STORAGE_BASE_URL: str = os.getenv("STORAGE_BASE_URL", "/storage")

    # Caching / Redis
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "")

    # Observability & Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", "")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_ROTATION_MAX_BYTES: int = int(os.getenv("LOG_ROTATION_MAX_BYTES", "10485760"))  # 10MB
    LOG_ROTATION_BACKUP_COUNT: int = int(os.getenv("LOG_ROTATION_BACKUP_COUNT", "5"))

    # Security Hardening & Networking
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    )
    ENFORCE_HTTPS: bool = os.getenv("ENFORCE_HTTPS", "false").lower() in ("true", "1", "yes")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

    def get_cors_origins(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
