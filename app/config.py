"""Application configuration management using Pydantic Settings.

Reads configuration from environment variables or .env file.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Apex Operations API."""

    # Application settings
    APP_NAME: str = "Apex Operations API"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL Database settings
    DB_HOST: str = "apex-db"
    DB_PORT: int = 5432
    DB_NAME: str = "apex_ops_db"
    DB_USER: str = "apex_user"
    DB_PASSWORD: str = "apex_secure_dev_password_change_me"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Optional override for the entire connection URL (e.g., in CI or SQLite tests)
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def get_database_url(self) -> str:
        """Construct the database URL if not explicitly provided."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
