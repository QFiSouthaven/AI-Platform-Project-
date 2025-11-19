"""
Configuration settings for the Data Integration module.

Uses Pydantic BaseSettings for environment variable management.
"""

import sys
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "data-integration"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8004

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_DEFAULT_TTL: int = 3600  # 1 hour in seconds

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "data-integration-group"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_ENABLE_AUTO_COMMIT: bool = True
    KAFKA_AUTO_COMMIT_INTERVAL_MS: int = 5000
    KAFKA_SESSION_TIMEOUT_MS: int = 30000
    KAFKA_MAX_POLL_RECORDS: int = 500

    # Kafka Topics to consume
    KAFKA_CONSUME_TOPICS: List[str] = [
        "gateway.user.created",
        "gateway.user.updated",
        "workflow.task.created",
        "workflow.task.completed",
        "workflow.task.failed",
        "processing.code.generated",
        "processing.code.optimized",
        "model.loaded",
        "model.unloaded",
    ]

    # Security
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    API_KEY_HEADER: str = "X-API-Key"

    # Event Processing
    EVENT_RETRY_MAX_ATTEMPTS: int = 3
    EVENT_RETRY_DELAY_SECONDS: int = 5
    EVENT_PROCESSING_TIMEOUT: int = 30

    # Cache Settings
    CACHE_KEY_PREFIX: str = "data_integration"
    CACHE_DEFAULT_TTL: int = 3600
    CACHE_MAX_KEYS: int = 10000

    # Metrics
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

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


# Global settings instance
settings = get_settings()
