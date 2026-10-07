import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "InsightX"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-super-secret-key-change-in-production-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Database
    DATABASE_URL: str = "sqlite:///./insightx.db"
    
    # Storage
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "data", "raw")
    PROCESSED_DIR: str = os.path.join(BASE_DIR, "data", "processed")
    SAMPLES_DIR: str = os.path.join(BASE_DIR, "data", "samples")
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # AI / LLM
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.0-flash"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.SAMPLES_DIR, exist_ok=True)
