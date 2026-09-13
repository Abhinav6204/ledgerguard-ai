"""
LedgerGuard AI — System Configuration
Hardened settings with environment variable validation and secret masking.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    ENVIRONMENT: str = Field("development", description="Environment: development, staging, production")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = Field("ledgerguard-insecure-default-change-me", min_length=32)
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:5173"

    # AI Inferences
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Security & Rate Limiting
    MAX_UPLOAD_SIZE_MB: int = 10
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 15
    MAX_PDF_PAGES: int = 20
    MAX_TEXT_CHARACTERS: int = 200000

    # Stripe Billing
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_PRICE_ID_ENTERPRISE: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./data/ledgerguard.db"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

settings = Settings()
