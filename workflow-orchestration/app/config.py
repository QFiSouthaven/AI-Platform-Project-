"""
Configuration settings for the Workflow Orchestration module.

Uses Pydantic Settings for environment variable management with validation.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "workflow-orchestration"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/workflow_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "workflow-orchestration-group"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"

    # Kafka Topics
    KAFKA_WORKFLOW_EVENTS_TOPIC: str = "workflow.events"
    KAFKA_TASK_EVENTS_TOPIC: str = "workflow.task.events"
    KAFKA_TASK_RESULTS_TOPIC: str = "workflow.task.results"

    # Security
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    # Scheduler
    SCHEDULER_MAX_WORKERS: int = 10
    SCHEDULER_JOB_COALESCE: bool = True
    SCHEDULER_MISFIRE_GRACE_TIME: int = 60

    # Workflow Defaults
    DEFAULT_WORKFLOW_TIMEOUT: int = 3600
    DEFAULT_TASK_TIMEOUT: int = 300
    DEFAULT_RETRY_COUNT: int = 3
    DEFAULT_RETRY_DELAY: int = 60

    # External Services
    CORE_PROCESSING_URL: str = "http://localhost:8003"
    DATA_INTEGRATION_URL: str = "http://localhost:8004"
    MODEL_MANAGEMENT_URL: str = "http://localhost:8005"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()


settings = get_settings()
