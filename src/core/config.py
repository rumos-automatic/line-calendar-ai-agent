"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # GCP Settings
    GOOGLE_CLOUD_PROJECT: str
    
    # Application
    PORT: int = 8000
    BASE_URL: str = "http://localhost:8000"
    
    # LINE Settings
    LINE_CHANNEL_SECRET: Optional[str] = None
    LINE_CHANNEL_ACCESS_TOKEN: Optional[str] = None
    LIFF_ID: Optional[str] = None
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = None
    
    # Firestore
    FIRESTORE_EMULATOR_HOST: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    USE_AI_AGENT: bool = True  # Toggle AI agent vs pattern matching
    
    # Vercel specific
    GOOGLE_SERVICE_ACCOUNT_KEY: Optional[str] = None  # JSON string
    
    # Secret Manager References (for Cloud Run)
    LINE_CHANNEL_SECRET_SM: Optional[str] = None
    LINE_CHANNEL_ACCESS_TOKEN_SM: Optional[str] = None
    GOOGLE_CLIENT_ID_SM: Optional[str] = None
    GOOGLE_CLIENT_SECRET_SM: Optional[str] = None
    ENCRYPTION_KEY_SM: Optional[str] = None
    OPENAI_API_KEY_SM: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **values):
        super().__init__(**values)
        
        # In production (Cloud Run), secrets are loaded from Secret Manager
        # For Vercel, all secrets are provided as environment variables
        if self.ENVIRONMENT == "production" and os.getenv("RUNTIME") != "vercel":
            from src.core.secrets import get_secret
            
            if self.LINE_CHANNEL_SECRET_SM and not self.LINE_CHANNEL_SECRET:
                self.LINE_CHANNEL_SECRET = get_secret(self.LINE_CHANNEL_SECRET_SM)
            
            if self.LINE_CHANNEL_ACCESS_TOKEN_SM and not self.LINE_CHANNEL_ACCESS_TOKEN:
                self.LINE_CHANNEL_ACCESS_TOKEN = get_secret(self.LINE_CHANNEL_ACCESS_TOKEN_SM)
            
            if self.GOOGLE_CLIENT_ID_SM and not self.GOOGLE_CLIENT_ID:
                self.GOOGLE_CLIENT_ID = get_secret(self.GOOGLE_CLIENT_ID_SM)
            
            if self.GOOGLE_CLIENT_SECRET_SM and not self.GOOGLE_CLIENT_SECRET:
                self.GOOGLE_CLIENT_SECRET = get_secret(self.GOOGLE_CLIENT_SECRET_SM)
            
            if self.ENCRYPTION_KEY_SM and not self.ENCRYPTION_KEY:
                self.ENCRYPTION_KEY = get_secret(self.ENCRYPTION_KEY_SM)
            
            if self.OPENAI_API_KEY_SM and not self.OPENAI_API_KEY:
                self.OPENAI_API_KEY = get_secret(self.OPENAI_API_KEY_SM)


# Create settings instance
settings = Settings()