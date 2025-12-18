from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    database_url: str = os.getenv("NEON_DATABASE_URL", "sqlite:///./test.db")

    # API Keys
    cohere_api_key: Optional[str] = os.getenv("COHERE_API_KEY")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")  # Optional if using Cohere for generation
    qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY")

    # Qdrant settings
    qdrant_cluster_endpoint: str = os.getenv("QDRANT_CLUSTER_ENDPOINT", "http://localhost:6333")

    # Application settings
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Optional settings
    language_model_provider: str = os.getenv("LANGUAGE_MODEL_PROVIDER", "cohere")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields that are not defined in the model


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()