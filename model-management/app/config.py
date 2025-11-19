"""
Configuration settings for Model Management module.

Uses Pydantic settings for environment variable management.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


def get_default_storage_path(subdir: str) -> str:
    """Get platform-appropriate default storage path."""
    if sys.platform == 'win32':
        # Use user's local app data on Windows
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return str(Path(base) / 'model-management' / subdir)
    else:
        return f"/data/{subdir}"


def get_default_temp_path() -> str:
    """Get platform-appropriate default temp path."""
    if sys.platform == 'win32':
        return str(Path(os.environ.get('TEMP', os.path.expanduser('~'))) / 'model-management')
    else:
        return "/tmp/model-management"


def get_default_encryption_key_path() -> str:
    """Get platform-appropriate default encryption key path."""
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return str(Path(base) / 'model-management' / 'secrets' / 'encryption.key')
    else:
        return "/secrets/encryption.key"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "model-management"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    WORKERS: int = 4

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "model_management"
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 100

    # Storage - Use platform-appropriate defaults
    MODEL_STORAGE_PATH: str = get_default_storage_path("models")
    PLUGIN_STORAGE_PATH: str = get_default_storage_path("plugins")
    TEMP_STORAGE_PATH: str = get_default_temp_path()
    MAX_MODEL_SIZE_MB: int = 10000  # 10GB
    ALLOWED_MODEL_EXTENSIONS: List[str] = [".pt", ".pth", ".h5", ".onnx", ".bin", ".safetensors", ".pkl"]

    # Encryption
    ENCRYPTION_KEY: Optional[str] = None
    ENCRYPTION_KEY_PATH: str = get_default_encryption_key_path()
    ENABLE_ENCRYPTION: bool = True
    KEY_ROTATION_DAYS: int = 90

    # Security
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    API_KEY_HEADER: str = "X-API-Key"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "model-management"
    KAFKA_CONSUMER_GROUP: str = "model-management-group"

    # Redis (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 3600

    # Model Loading
    MODEL_LOAD_TIMEOUT_SECONDS: int = 300
    MAX_LOADED_MODELS: int = 10
    MODEL_CACHE_SIZE_MB: int = 5000

    # Versioning
    MAX_VERSIONS_PER_MODEL: int = 100
    AUTO_CLEANUP_OLD_VERSIONS: bool = True
    KEEP_LAST_N_VERSIONS: int = 10

    # Health Check
    HEALTH_CHECK_PATH: str = "/health"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


# Create directories on import
settings = get_settings()
Path(settings.MODEL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.PLUGIN_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.TEMP_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
