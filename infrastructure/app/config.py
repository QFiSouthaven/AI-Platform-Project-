"""
Infrastructure Module - Configuration Management

This module defines all configuration settings using Pydantic Settings
for type validation and environment variable loading.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application settings
    APP_NAME: str = "infrastructure-module"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8006

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]

    # Ray cluster settings
    RAY_ADDRESS: str = "auto"
    RAY_NAMESPACE: str = "ai-platform"
    RAY_NUM_CPUS: Optional[int] = None
    RAY_NUM_GPUS: Optional[int] = None
    RAY_OBJECT_STORE_MEMORY: Optional[int] = None
    RAY_DASHBOARD_HOST: str = "0.0.0.0"
    RAY_DASHBOARD_PORT: int = 8265
    RAY_TEMP_DIR: str = "/tmp/ray"
    RAY_LOG_TO_DRIVER: bool = True
    RAY_INCLUDE_DASHBOARD: bool = True

    # Task execution settings
    TASK_DEFAULT_TIMEOUT: int = 300  # seconds
    TASK_MAX_RETRIES: int = 3
    TASK_RETRY_DELAY: int = 5  # seconds
    TASK_QUEUE_MAX_SIZE: int = 10000
    TASK_RESULT_TTL: int = 3600  # seconds

    # Worker settings
    MIN_WORKERS: int = 1
    MAX_WORKERS: int = 10
    WORKERS_PER_NODE: int = 4
    WORKER_CPU_FRACTION: float = 0.25
    WORKER_MEMORY_MB: int = 1024
    WORKER_IDLE_TIMEOUT: int = 300  # seconds

    # Auto-scaling settings
    AUTOSCALE_ENABLED: bool = True
    AUTOSCALE_CHECK_INTERVAL: int = 30  # seconds
    AUTOSCALE_COOLDOWN_PERIOD: int = 120  # seconds
    AUTOSCALE_CPU_THRESHOLD_HIGH: float = 80.0
    AUTOSCALE_CPU_THRESHOLD_LOW: float = 30.0
    AUTOSCALE_MEMORY_THRESHOLD_HIGH: float = 85.0
    AUTOSCALE_MEMORY_THRESHOLD_LOW: float = 40.0
    AUTOSCALE_QUEUE_THRESHOLD: int = 100
    AUTOSCALE_SCALE_UP_INCREMENT: int = 2
    AUTOSCALE_SCALE_DOWN_INCREMENT: int = 1

    # Health monitoring settings
    HEALTH_CHECK_INTERVAL: int = 15  # seconds
    HEALTH_CHECK_TIMEOUT: int = 10  # seconds
    HEALTH_FAILURE_THRESHOLD: int = 3
    HEALTH_RECOVERY_THRESHOLD: int = 2

    # Resource management settings
    RESOURCE_RESERVATION_TIMEOUT: int = 60  # seconds
    RESOURCE_CLEANUP_INTERVAL: int = 300  # seconds

    # Metrics settings
    METRICS_ENABLED: bool = True
    METRICS_COLLECTION_INTERVAL: int = 10  # seconds
    METRICS_RETENTION_PERIOD: int = 86400  # seconds (24 hours)
    METRICS_AGGREGATION_INTERVAL: int = 60  # seconds

    # Redis settings (for distributed state)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PREFIX: str = "infrastructure:"
    REDIS_TTL: int = 3600

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "infrastructure"
    KAFKA_CONSUMER_GROUP: str = "infrastructure-consumers"

    # Security settings
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    API_KEY_HEADER: str = "X-API-Key"

    # NGINX settings
    NGINX_UPSTREAM_NAME: str = "infrastructure_backend"
    NGINX_MAX_CONNECTIONS: int = 1000
    NGINX_KEEPALIVE: int = 32

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
