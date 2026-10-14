"""Application configuration management using Pydantic Settings.

Reads configuration values from environment variables or .env file,
ensuring secrets and runtime settings are never hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema and environment variable loader."""

    # Project metadata
    PROJECT_NAME: str = "Fitness Studio Booking API"
    VERSION: str = "1.0.0"

    # Database settings
    # Default is a local SQLite database file in the project root
    DATABASE_URL: str = "sqlite:///./fitness_studio.db"

    # JWT Authentication settings
    # In production, SECRET_KEY must be provided via an environment variable
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Global settings singleton
settings = Settings()
