"""
Configuration settings for Core Processing module.

Uses Pydantic settings for environment variable management and validation.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "core-processing"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # LLM Configuration
    MODEL_NAME: str = "bigcode/starcoder"
    HF_API_TOKEN: Optional[str] = None
    USE_GPU: bool = True
    MAX_SEQUENCE_LENGTH: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.95
    TOP_K: int = 50
    REPETITION_PENALTY: float = 1.1
    DO_SAMPLE: bool = True
    NUM_RETURN_SEQUENCES: int = 1

    # Model Loading
    MODEL_CACHE_DIR: str = "/tmp/model_cache"
    LOAD_IN_8BIT: bool = False
    LOAD_IN_4BIT: bool = False
    DEVICE_MAP: str = "auto"
    TORCH_DTYPE: str = "float16"

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "core-processing-group"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_ENABLE_AUTO_COMMIT: bool = True

    # Kafka Topics
    KAFKA_TOPIC_GENERATION_REQUEST: str = "processing.code.generation.request"
    KAFKA_TOPIC_GENERATION_RESULT: str = "processing.code.generation.result"
    KAFKA_TOPIC_DEBUG_REQUEST: str = "processing.code.debug.request"
    KAFKA_TOPIC_DEBUG_RESULT: str = "processing.code.debug.result"
    KAFKA_TOPIC_OPTIMIZE_REQUEST: str = "processing.code.optimize.request"
    KAFKA_TOPIC_OPTIMIZE_RESULT: str = "processing.code.optimize.result"
    KAFKA_TOPIC_EVALUATE_REQUEST: str = "processing.code.evaluate.request"
    KAFKA_TOPIC_EVALUATE_RESULT: str = "processing.code.evaluate.result"

    # Redis Configuration (for caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 3600  # 1 hour

    # Security
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    API_KEY_HEADER: str = "X-API-Key"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Timeouts
    INFERENCE_TIMEOUT: int = 120  # seconds
    KAFKA_TIMEOUT: int = 30  # seconds

    # GPU Memory Management
    MAX_GPU_MEMORY_MB: Optional[int] = None
    CLEAR_CACHE_THRESHOLD: float = 0.9  # Clear cache when GPU memory > 90%

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
