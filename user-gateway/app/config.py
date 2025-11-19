"""
Configuration module for User Gateway.

Loads environment variables and provides settings for the application.
Windows 11 compatible with pathlib for cross-platform path handling.
"""

import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings

# Base directory of the module
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Platform detection
IS_WINDOWS = sys.platform == "win32"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "user-gateway"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ai_platform"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL: int = 3600

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "gateway"
    KAFKA_PRODUCER_TIMEOUT: int = 10

    # Security
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password hashing
    PASSWORD_HASH_ROUNDS: int = 12

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # OAuth2
    OAUTH2_TOKEN_URL: str = "/api/v1/auth/login"

    # File paths (use pathlib for Windows compatibility)
    LOG_DIR: Optional[str] = None
    UPLOAD_DIR: Optional[str] = None
    TEMP_DIR: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def log_path(self) -> Path:
        """Get log directory path (Windows compatible)."""
        if self.LOG_DIR:
            return Path(self.LOG_DIR)
        return BASE_DIR / "logs"

    @property
    def upload_path(self) -> Path:
        """Get upload directory path (Windows compatible)."""
        if self.UPLOAD_DIR:
            return Path(self.UPLOAD_DIR)
        return BASE_DIR / "uploads"

    @property
    def temp_path(self) -> Path:
        """Get temp directory path (Windows compatible)."""
        if self.TEMP_DIR:
            return Path(self.TEMP_DIR)
        if IS_WINDOWS:
            import tempfile
            return Path(tempfile.gettempdir()) / "user-gateway"
        return Path("/tmp/user-gateway")

    def get_database_url_sync(self) -> str:
        """
        Get synchronous database URL for tools like Alembic.

        Converts asyncpg URL to psycopg2 for sync operations.
        Handles Windows-specific path considerations.
        """
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()


settings = get_settings()
