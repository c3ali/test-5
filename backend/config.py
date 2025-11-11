# backend/config.py
"""
Gestion centralisée de la configuration et des variables d'environnement.
Utilise Pydantic BaseSettings pour la validation et le chargement des variables.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator, AnyHttpUrl
from dotenv import load_dotenv

# Chargement du fichier .env si présent
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration de l'application.
    Les valeurs sont chargées depuis les variables d'environnement.
    """
    
    # ============================================
    # ENVIRONMENT & GENERAL
    # ============================================
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    APP_NAME: str = "MonAPI"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # ============================================
    # SECURITY
    # ============================================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 jours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 jours
    
    # CORS
    ALLOWED_ORIGINS: List[AnyHttpUrl] = []
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # ============================================
    # DATABASE
    # ============================================
    # PostgreSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "monapi_dev"
    
    # URL de connexion complète (alternative)
    DATABASE_URL: Optional[str] = None
    
    # Configuration SQLAlchemy
    SQLALCHEMY_POOL_SIZE: int = 10
    SQLALCHEMY_MAX_OVERFLOW: int = 20
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 3600
    
    # ============================================
    # REDIS
    # ============================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_SSL: bool = False
    REDIS_URL: Optional[str] = None
    
    # ============================================
    # JWT & AUTHENTIFICATION
    # ============================================
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "monapi"
    JWT_AUDIENCE: str = "monapi-users"
    
    # ============================================
    # EMAIL
    # ============================================
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    FROM_EMAIL: Optional[str] = None
    
    # ============================================
    # LOGGING
    # ============================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_FILE_BACKUP_COUNT: int = 5
    
    # ============================================
    # FILE STORAGE
    # ============================================
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    
    # Cloud Storage (AWS S3)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_REGION: str = "eu-west-3"
    AWS_S3_ENDPOINT_URL: Optional[str] = None
    
    # ============================================
    # THIRD-PARTY APIs
    # ============================================
    # Stripe
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Google
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # GitHub
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    # ============================================
    # MONITORING
    # ============================================
    SENTRY_DSN: Optional[str] = None
    TELEMETRY_ENABLED: bool = False
    
    # ============================================
    # FEATURE FLAGS
    # ============================================
    ENABLE_REGISTRATION: bool = True
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_RATE_LIMITING: bool = True
    
    # ============================================
    # VALIDATION
    # ============================================
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Valide que l'environnement est autorisé."""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"L'environnement doit être l'un des suivants: {allowed_envs}")
        return v
    
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        """Vérifie que la clé secrète n'est pas la valeur par défaut en production."""
        if os.getenv("ENVIRONMENT") == "production" and v == "change-this-secret-key-in-production":
            raise ValueError("Il est impératif de définir une SECRET_KEY sécurisée en production")
        return v
    
    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_database_url(cls, v, values):
        """Construit l'URL de connexion à la base de données si non fournie."""
        if isinstance(v, str) and v:
            return v
        
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )
    
    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_url(cls, v, values):
        """Construit l'URL de connexion Redis si non fournie."""
        if isinstance(v, str) and v:
            return v
        
        password = values.get("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""
        proto = "rediss" if values.get("REDIS_SSL") else "redis"
        host = values.get("REDIS_HOST")
        port = values.get("REDIS_PORT")
        db = values.get("REDIS_DB")
        
        return f"{proto}://{auth}{host}:{port}/{db}"
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse la liste des origines autorisées depuis une chaîne ou la retourne telle quelle."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Parse comme liste JSON
                import json
                return json.loads(v)
            elif "," in v:
                # Parse comme liste séparée par des virgules
                return [origin.strip() for origin in v.split(",")]
        return v or []
    
    # ============================================
    # CONFIGURATION PYDANTIC
    # ============================================
    class Config:
        """Configuration du modèle Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True  # Respecte la casse des variables d'environnement
        
        # Permet de charger des variables avec préfixe
        env_prefix = "APP_"
        
        # Pour les champs avec alias (ex: SECRET_KEY = Field(alias="SECRET"))
        allow_population_by_field_name = True


# ============================================
# EXPORT DE L'INSTANCE
# ============================================
# Instance globale de la configuration
settings = Settings()

# ============================================
# UTILITAIRES
# ============================================
def get_settings() -> Settings:
    """
    Retourne l'instance des paramètres.
    Utilisé pour l'injection de dépendances dans FastAPI.
    """
    return settings

# ============================================
# EXEMPLE D'UTILISATION
# ============================================
if __name__ == "__main__":
    # Affiche la configuration chargée (masque les secrets)
    print(f"Configuration chargée pour l'environnement : {settings.ENVIRONMENT}")
    print(f"Debug : {settings.DEBUG}")
    print(f"Database URL : {settings.DATABASE_URL}")
    print(f"Redis URL : {settings.REDIS_URL}")
    print(f"Log Level : {settings.LOG_LEVEL}")
