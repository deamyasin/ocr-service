from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    # API Settings
    API_KEY_NAME: str = "X-API-Key"
    API_KEY: str = "your-secret-api-key"  # Change this in production
    
    # Processing Settings
    DEFAULT_CORE_COUNT: int = 1
    MAX_CORE_COUNT: int = os.cpu_count() or 1
    BATCH_SIZE: int = 10
    
    # Storage Settings
    UPLOAD_DIR: Path = Path("uploads")
    OUTPUT_DIR: Path = Path("outputs")
    TEMP_DIR: Path = Path("temp")
    
    # Redis Settings for Queue
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # OCR Settings
    SUPPORTED_LANGUAGES: List[str] = [
        "ind",  # Indonesian
        "eng",  # English
        "fra",  # French
        "deu",  # German
        "spa",  # Spanish
        "ita",  # Italian
        "por",  # Portuguese
        "rus",  # Russian
        "chi_sim",  # Simplified Chinese
        "chi_tra",  # Traditional Chinese
        "jpn",  # Japanese
        "kor",  # Korean
        "ara",  # Arabic
        "hin",  # Hindi
    ]
    
    DEFAULT_LANGUAGE: str = "ind"
    
    # OCR Quality Settings
    OCR_DPI: int = 300
    OCR_QUALITY: int = 100
    
    # File Processing Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    SUPPORTED_INPUT_FORMATS: List[str] = [".pdf", ".docx", ".doc"]
    
    class Config:
        env_file = ".env"

    def create_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [self.UPLOAD_DIR, self.OUTPUT_DIR, self.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.create_directories() 