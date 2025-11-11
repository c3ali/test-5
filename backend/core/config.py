"""
Application configuration settings
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Kanban Board API"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    # Use SQLite by default for simplicity. For production with PostgreSQL, set DATABASE_URL env var.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kanban.db")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-please-use-a-strong-random-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
