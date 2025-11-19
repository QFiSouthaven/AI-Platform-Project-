"""
Shared constants for all AI Platform modules.

This module contains constants used across multiple services to ensure
consistency in API versions, status codes, event types, and more.
"""

from enum import Enum

# ============================================================================
# API Versioning
# ============================================================================

API_VERSION_V1 = "v1"
API_VERSION_V2 = "v2"
CURRENT_API_VERSION = API_VERSION_V1
API_PREFIX = f"/api/{CURRENT_API_VERSION}"


# ============================================================================
# HTTP Status Codes
# ============================================================================

class HTTPStatus:
    """Standard HTTP status codes."""

    # Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    # Redirection
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304

    # Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429

    # Server errors
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


# ============================================================================
# Application Status
# ============================================================================

class AppStatus(str, Enum):
    """Application response status values."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Workflow Status
# ============================================================================

class WorkflowStatus(str, Enum):
    """Workflow execution status values."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskStatus(str, Enum):
    """Task execution status values."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


# ============================================================================
# Model Status
# ============================================================================

class ModelStatus(str, Enum):
    """AI model status values."""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    AVAILABLE = "available"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelType(str, Enum):
    """Types of AI models."""

    CLASSIFICATION = "classification"
    GENERATION = "generation"
    EMBEDDING = "embedding"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    QUESTION_ANSWERING = "question_answering"
    CUSTOM = "custom"


class ModelFramework(str, Enum):
    """AI model frameworks."""

    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    JAX = "jax"
    HUGGINGFACE = "huggingface"


# ============================================================================
# Kafka Topics
# ============================================================================

class KafkaTopics:
    """Kafka topic names following the naming convention: {module}.{entity}.{action}"""

    # User Gateway topics
    GATEWAY_USER_CREATED = "gateway.user.created"
    GATEWAY_USER_UPDATED = "gateway.user.updated"
    GATEWAY_USER_DELETED = "gateway.user.deleted"
    GATEWAY_AUTH_LOGIN = "gateway.auth.login"
    GATEWAY_AUTH_LOGOUT = "gateway.auth.logout"
    GATEWAY_API_REQUEST = "gateway.api.request"

    # Workflow Orchestration topics
    WORKFLOW_CREATED = "workflow.workflow.created"
    WORKFLOW_STARTED = "workflow.workflow.started"
    WORKFLOW_COMPLETED = "workflow.workflow.completed"
    WORKFLOW_FAILED = "workflow.workflow.failed"
    WORKFLOW_TASK_STARTED = "workflow.task.started"
    WORKFLOW_TASK_COMPLETED = "workflow.task.completed"
    WORKFLOW_TASK_FAILED = "workflow.task.failed"

    # Core Processing topics
    PROCESSING_JOB_CREATED = "processing.job.created"
    PROCESSING_JOB_STARTED = "processing.job.started"
    PROCESSING_JOB_COMPLETED = "processing.job.completed"
    PROCESSING_JOB_FAILED = "processing.job.failed"
    PROCESSING_CODE_GENERATED = "processing.code.generated"

    # Data Integration topics
    DATA_EVENT_RECEIVED = "data.event.received"
    DATA_EVENT_PROCESSED = "data.event.processed"
    DATA_CACHE_UPDATED = "data.cache.updated"
    DATA_CACHE_INVALIDATED = "data.cache.invalidated"

    # Model Management topics
    MODEL_UPLOADED = "model.model.uploaded"
    MODEL_LOADED = "model.model.loaded"
    MODEL_UNLOADED = "model.model.unloaded"
    MODEL_DELETED = "model.model.deleted"
    MODEL_VERSION_CREATED = "model.version.created"

    # Infrastructure topics
    INFRA_SCALING_UP = "infra.scaling.up"
    INFRA_SCALING_DOWN = "infra.scaling.down"
    INFRA_HEALTH_CHECK = "infra.health.check"
    INFRA_RESOURCE_ALLOCATED = "infra.resource.allocated"


# ============================================================================
# Error Codes
# ============================================================================

class ErrorCodes:
    """Standard error codes for the platform."""

    # Authentication errors (1xxx)
    AUTH_INVALID_CREDENTIALS = "AUTH_1001"
    AUTH_TOKEN_EXPIRED = "AUTH_1002"
    AUTH_TOKEN_INVALID = "AUTH_1003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_1004"
    AUTH_USER_NOT_FOUND = "AUTH_1005"
    AUTH_USER_DISABLED = "AUTH_1006"

    # Validation errors (2xxx)
    VALIDATION_ERROR = "VAL_2001"
    VALIDATION_MISSING_FIELD = "VAL_2002"
    VALIDATION_INVALID_FORMAT = "VAL_2003"
    VALIDATION_OUT_OF_RANGE = "VAL_2004"

    # Resource errors (3xxx)
    RESOURCE_NOT_FOUND = "RES_3001"
    RESOURCE_ALREADY_EXISTS = "RES_3002"
    RESOURCE_CONFLICT = "RES_3003"
    RESOURCE_LOCKED = "RES_3004"

    # Workflow errors (4xxx)
    WORKFLOW_NOT_FOUND = "WF_4001"
    WORKFLOW_INVALID_STATE = "WF_4002"
    WORKFLOW_EXECUTION_FAILED = "WF_4003"
    WORKFLOW_TASK_FAILED = "WF_4004"
    WORKFLOW_TIMEOUT = "WF_4005"
    WORKFLOW_CYCLE_DETECTED = "WF_4006"

    # Model errors (5xxx)
    MODEL_NOT_FOUND = "MDL_5001"
    MODEL_LOAD_FAILED = "MDL_5002"
    MODEL_INFERENCE_FAILED = "MDL_5003"
    MODEL_INVALID_FORMAT = "MDL_5004"
    MODEL_VERSION_CONFLICT = "MDL_5005"

    # Processing errors (6xxx)
    PROCESSING_FAILED = "PROC_6001"
    PROCESSING_TIMEOUT = "PROC_6002"
    PROCESSING_INVALID_INPUT = "PROC_6003"
    PROCESSING_RESOURCE_EXHAUSTED = "PROC_6004"

    # External service errors (7xxx)
    KAFKA_CONNECTION_ERROR = "EXT_7001"
    REDIS_CONNECTION_ERROR = "EXT_7002"
    DATABASE_CONNECTION_ERROR = "EXT_7003"
    EXTERNAL_API_ERROR = "EXT_7004"

    # Internal errors (9xxx)
    INTERNAL_ERROR = "INT_9001"
    NOT_IMPLEMENTED = "INT_9002"
    SERVICE_UNAVAILABLE = "INT_9003"


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimits:
    """Rate limiting configuration."""

    # Requests per minute
    DEFAULT_RATE_LIMIT = 60
    AUTH_RATE_LIMIT = 10
    API_RATE_LIMIT = 100
    WEBHOOK_RATE_LIMIT = 30

    # Burst limits
    DEFAULT_BURST = 10
    AUTH_BURST = 3
    API_BURST = 20


# ============================================================================
# Pagination
# ============================================================================

class Pagination:
    """Pagination configuration."""

    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1


# ============================================================================
# Cache Configuration
# ============================================================================

class CacheTTL:
    """Cache TTL values in seconds."""

    SHORT = 60  # 1 minute
    MEDIUM = 300  # 5 minutes
    LONG = 3600  # 1 hour
    VERY_LONG = 86400  # 24 hours

    # Specific cache TTLs
    USER_SESSION = 1800  # 30 minutes
    API_RESPONSE = 300  # 5 minutes
    MODEL_METADATA = 3600  # 1 hour
    WORKFLOW_STATUS = 60  # 1 minute


# ============================================================================
# Service Ports
# ============================================================================

class ServicePorts:
    """Default ports for services."""

    USER_GATEWAY = 8001
    WORKFLOW_ORCHESTRATION = 8002
    CORE_PROCESSING = 8003
    DATA_INTEGRATION = 8004
    MODEL_MANAGEMENT = 8005
    INFRASTRUCTURE = 8006

    # Infrastructure services
    POSTGRESQL = 5432
    MONGODB = 27017
    REDIS = 6379
    KAFKA = 9092
    ZOOKEEPER = 2181


# ============================================================================
# JWT Configuration
# ============================================================================

class JWTConfig:
    """JWT token configuration."""

    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    TOKEN_TYPE = "Bearer"


# ============================================================================
# File Upload Configuration
# ============================================================================

class FileUpload:
    """File upload configuration."""

    MAX_FILE_SIZE_MB = 100
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {
        "model": [".pt", ".pth", ".h5", ".pkl", ".onnx", ".bin"],
        "data": [".json", ".csv", ".parquet", ".txt"],
        "config": [".yaml", ".yml", ".json", ".toml"],
    }


# ============================================================================
# Message Schema Versions
# ============================================================================

KAFKA_SCHEMA_VERSION = "1.0"
API_SCHEMA_VERSION = "1.0"


# ============================================================================
# Health Check Configuration
# ============================================================================

class HealthCheck:
    """Health check configuration."""

    INTERVAL_SECONDS = 30
    TIMEOUT_SECONDS = 5
    UNHEALTHY_THRESHOLD = 3
    HEALTHY_THRESHOLD = 2
