from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv
import secrets
import base64

# Load environment variables from the details.env file
load_dotenv('details.env')

def generate_jwt_secret():
    """Generate a secure JWT secret if one is not provided"""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

class Settings(BaseSettings):
    # Google OAuth settings
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    
    # JWT settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    
    # Database settings
    database_url: str = "sqlite:///./email_flags.db"
    
    # AI API keys
    openai_api_key: str
    gemini_api_key: str
    
    class Config:
        env_file = "details.env"

    def get_masked_value(self, value: str) -> str:
        """Return a masked version of sensitive values"""
        if not value or value.startswith("${"):
            return "not_set"
        return f"{value[:4]}...{value[-4:]}"
    
    def check_configuration(self) -> dict:
        """Check if all required configuration is set"""
        return {
            "google_client_id": self.get_masked_value(self.google_client_id),
            "google_client_secret": self.get_masked_value(self.google_client_secret),
            "google_redirect_uri": self.google_redirect_uri,
            "openai_api_key": self.get_masked_value(self.openai_api_key),
            "gemini_api_key": self.get_masked_value(self.gemini_api_key),
            "jwt_secret": "is_set" if self.jwt_secret and not self.jwt_secret.startswith("${") else "not_set",
            "database_url": self.database_url
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 