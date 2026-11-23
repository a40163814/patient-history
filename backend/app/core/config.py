import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/ayush_intake.db"
    DATABASE_SYNC_URL: str = f"sqlite:///{BASE_DIR}/ayush_intake.db"

    # Security
    SECRET_KEY: str = "ayush-dev-secret-key-safety-minded-health-tech-min32"
    SESSION_EXPIRE_MINUTES: int = 1440
    ALLOW_TRANSCRIPT_STORAGE: bool = True
    DATA_RETENTION_DAYS: int = 30

    # AI Model Configuration (never hardcoded, pulled from env)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_LIVE_MODEL: str = "gemini-2.5-flash-native-audio-latest"
    GEMINI_TEXT_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_SAFETY_MODEL: str = "gemini-3.1-flash-lite"

    @property
    def is_gemini_configured(self) -> bool:
        if not self.GEMINI_API_KEY:
            return False
        clean = self.GEMINI_API_KEY.strip()
        return bool(clean and not clean.startswith("your_") and clean != "your_gemini_api_key_here")

    # Bhashini Pipeline
    BHASHINI_USER_ID: str = "mock_bhashini_user"
    BHASHINI_API_KEY: str = "mock_bhashini_key"
    BHASHINI_PIPELINE_ID: str = "mock_pipeline"
    BHASHINI_INFERENCE_ENDPOINT: str = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    # Triage and Safety Hotlines
    CRISIS_HELPLINE_NUMBER: str = "14416"
    CRISIS_HELPLINE_NAME: str = "Tele-MANAS (Mental Health) / Emergency 112"
    EMERGENCY_AMBULANCE_NUMBER: str = "108"

    # Directories
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    PDF_OUTPUT_DIR: Path = BASE_DIR / "generated_pdfs"
    CONFIG_DIR: Path = BASE_DIR / "config"
    PROMPTS_DIR: Path = BASE_DIR / "prompts"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PDF_OUTPUT_DIR, exist_ok=True)
