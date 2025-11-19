"""
Shared utilities and configurations for AI Platform modules.

This package contains common code shared across all AI Platform services:
- logging_config: Structured logging configuration
- constants: Shared constants and enums
- exceptions: Custom exception classes
"""

from shared.constants import (
    API_PREFIX,
    CURRENT_API_VERSION,
    AppStatus,
    CacheTTL,
    ErrorCodes,
    HTTPStatus,
    JWTConfig,
    KafkaTopics,
    ModelFramework,
    ModelStatus,
    ModelType,
    Pagination,
    RateLimits,
    ServicePorts,
    TaskStatus,
    WorkflowStatus,
)
from shared.exceptions import (
    AIplatformException,
    AuthenticationError,
    DatabaseConnectionError,
    ExternalServiceError,
    InvalidCredentialsError,
    InvalidTokenError,
    KafkaConnectionError,
    ModelError,
    ModelInferenceError,
    ModelLoadError,
    ModelNotFoundError,
    ProcessingError,
    RateLimitExceededError,
    RedisConnectionError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    TaskExecutionError,
    TokenExpiredError,
    ValidationError,
    WorkflowError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)
from shared.logging_config import (
    bind_correlation_id,
    clear_correlation_id,
    configure_logging,
    get_logger,
    log_database_operation,
    log_kafka_message,
    log_request,
)

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    "bind_correlation_id",
    "clear_correlation_id",
    "log_request",
    "log_kafka_message",
    "log_database_operation",
    # Constants
    "API_PREFIX",
    "CURRENT_API_VERSION",
    "HTTPStatus",
    "AppStatus",
    "WorkflowStatus",
    "TaskStatus",
    "ModelStatus",
    "ModelType",
    "ModelFramework",
    "KafkaTopics",
    "ErrorCodes",
    "RateLimits",
    "Pagination",
    "CacheTTL",
    "ServicePorts",
    "JWTConfig",
    # Exceptions
    "AIplatformException",
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "ValidationError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowExecutionError",
    "TaskExecutionError",
    "ModelError",
    "ModelNotFoundError",
    "ModelLoadError",
    "ModelInferenceError",
    "ProcessingError",
    "ExternalServiceError",
    "KafkaConnectionError",
    "RedisConnectionError",
    "DatabaseConnectionError",
    "RateLimitExceededError",
]

__version__ = "1.0.0"
