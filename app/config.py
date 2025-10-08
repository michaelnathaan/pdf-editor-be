from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    HOST: str
    PORT: int
    
    # API Authentication
    API_SECRET_KEY: str
    SESSION_SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    
    # Storage
    STORAGE_PATH: str
    UPLOAD_MAX_SIZE: int
    ALLOWED_UPLOAD_EXTENSIONS: List[str]
    ALLOWED_IMAGE_EXTENSIONS: List[str]
    
    # Session Configuration
    SESSION_EXPIRY_HOURS: int
    SESSION_CLEANUP_INTERVAL_MINUTES: int
    
    # CORS
    CORS_ORIGINS: List[str]
    
    # Webhook
    WEBHOOK_TIMEOUT_SECONDS: int = 30
    WEBHOOK_RETRY_ATTEMPTS: int = 3
    
    @property
    def upload_dir(self) -> str:
        return os.path.join(self.STORAGE_PATH, "uploads")
    
    @property
    def edited_dir(self) -> str:
        return os.path.join(self.STORAGE_PATH, "edited")
    
    @property
    def temp_dir(self) -> str:
        return os.path.join(self.STORAGE_PATH, "temp")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

# Create storage directories if they don't exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.edited_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)