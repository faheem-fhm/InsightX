import os

base = r'C:\Users\HP\.gemini\antigravity\scratch\InsightX\backend\app\core'
os.makedirs(base, exist_ok=True)

config_py = """import os
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
"""

logging_py = """import logging
import sys

def setup_logger(name: str = "insightx") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()
"""

exceptions_py = """from typing import Any, Optional, Dict
from fastapi import HTTPException, status

class InsightXException(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class DatasetNotFoundError(InsightXException):
    def __init__(self, dataset_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID '{dataset_id}' was not found."
        )

class InvalidFileFormatError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or unsupported file format: {message}"
        )

class FileSizeExceededError(InsightXException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds allowed limit of {max_mb}MB."
        )

class PreprocessingError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data preprocessing failed: {message}"
        )

class UnsafeSQLError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security policy violation: Generated query contains prohibited operations. {message}"
        )

class MLWorkflowError(InsightXException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Machine learning computation error: {message}"
        )
"""

init_py = """from .config import settings
from .logging import logger
from .exceptions import (
    InsightXException,
    DatasetNotFoundError,
    InvalidFileFormatError,
    FileSizeExceededError,
    PreprocessingError,
    UnsafeSQLError,
    MLWorkflowError
)

__all__ = [
    "settings",
    "logger",
    "InsightXException",
    "DatasetNotFoundError",
    "InvalidFileFormatError",
    "FileSizeExceededError",
    "PreprocessingError",
    "UnsafeSQLError",
    "MLWorkflowError"
]
"""

with open(os.path.join(base, "config.py"), "w", encoding="utf-8") as f:
    f.write(config_py)

with open(os.path.join(base, "logging.py"), "w", encoding="utf-8") as f:
    f.write(logging_py)

with open(os.path.join(base, "exceptions.py"), "w", encoding="utf-8") as f:
    f.write(exceptions_py)

with open(os.path.join(base, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(init_py)

print("Backend core modules successfully created.")
