"""
Shared custom exceptions for all AI Platform modules.

This module defines custom exception classes that provide consistent
error handling across all services with proper error codes and messages.
"""

from typing import Any

from shared.constants import ErrorCodes, HTTPStatus


class AIplatformException(Exception):
    """
    Base exception for all AI Platform errors.

    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code.
        status_code: HTTP status code.
        details: Additional error details.
    """

    def __init__(
        self,
        message: str,
        error_code: str = ErrorCodes.INTERNAL_ERROR,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


# ============================================================================
# Authentication Exceptions
# ============================================================================

class AuthenticationError(AIplatformException):
    """Base exception for authentication errors."""

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = ErrorCodes.AUTH_INVALID_CREDENTIALS,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.UNAUTHORIZED,
            details=details,
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message="Invalid username or password",
            error_code=ErrorCodes.AUTH_INVALID_CREDENTIALS,
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when a token has expired."""

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message="Token has expired",
            error_code=ErrorCodes.AUTH_TOKEN_EXPIRED,
            details=details,
        )


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid."""

    def __init__(self, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message="Invalid token",
            error_code=ErrorCodes.AUTH_TOKEN_INVALID,
            details=details,
        )


class InsufficientPermissionsError(AIplatformException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCodes.AUTH_INSUFFICIENT_PERMISSIONS,
            status_code=HTTPStatus.FORBIDDEN,
            details=details,
        )


class UserNotFoundError(AuthenticationError):
    """Raised when user is not found."""

    def __init__(self, user_id: str | None = None) -> None:
        details = {"user_id": user_id} if user_id else None
        super().__init__(
            message="User not found",
            error_code=ErrorCodes.AUTH_USER_NOT_FOUND,
            details=details,
        )


class UserDisabledError(AuthenticationError):
    """Raised when user account is disabled."""

    def __init__(self, user_id: str | None = None) -> None:
        details = {"user_id": user_id} if user_id else None
        super().__init__(
            message="User account is disabled",
            error_code=ErrorCodes.AUTH_USER_DISABLED,
            details=details,
        )


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(AIplatformException):
    """Base exception for validation errors."""

    def __init__(
        self,
        message: str = "Validation error",
        error_code: str = ErrorCodes.VALIDATION_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details=details,
        )


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(self, field_name: str) -> None:
        super().__init__(
            message=f"Missing required field: {field_name}",
            error_code=ErrorCodes.VALIDATION_MISSING_FIELD,
            details={"field": field_name},
        )


class InvalidFormatError(ValidationError):
    """Raised when a field has invalid format."""

    def __init__(self, field_name: str, expected_format: str) -> None:
        super().__init__(
            message=f"Invalid format for field '{field_name}'. Expected: {expected_format}",
            error_code=ErrorCodes.VALIDATION_INVALID_FORMAT,
            details={"field": field_name, "expected_format": expected_format},
        )


class OutOfRangeError(ValidationError):
    """Raised when a value is out of acceptable range."""

    def __init__(
        self,
        field_name: str,
        min_value: Any = None,
        max_value: Any = None,
    ) -> None:
        message = f"Value for '{field_name}' is out of range"
        if min_value is not None and max_value is not None:
            message += f" (must be between {min_value} and {max_value})"
        elif min_value is not None:
            message += f" (must be at least {min_value})"
        elif max_value is not None:
            message += f" (must be at most {max_value})"

        super().__init__(
            message=message,
            error_code=ErrorCodes.VALIDATION_OUT_OF_RANGE,
            details={
                "field": field_name,
                "min_value": min_value,
                "max_value": max_value,
            },
        )


# ============================================================================
# Resource Exceptions
# ============================================================================

class ResourceNotFoundError(AIplatformException):
    """Raised when a resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
    ) -> None:
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            message=message,
            error_code=ErrorCodes.RESOURCE_NOT_FOUND,
            status_code=HTTPStatus.NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceAlreadyExistsError(AIplatformException):
    """Raised when a resource already exists."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
    ) -> None:
        message = f"{resource_type} already exists"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            message=message,
            error_code=ErrorCodes.RESOURCE_ALREADY_EXISTS,
            status_code=HTTPStatus.CONFLICT,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceConflictError(AIplatformException):
    """Raised when there's a resource conflict."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCodes.RESOURCE_CONFLICT,
            status_code=HTTPStatus.CONFLICT,
            details=details,
        )


class ResourceLockedError(AIplatformException):
    """Raised when a resource is locked."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
    ) -> None:
        message = f"{resource_type} is locked"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            message=message,
            error_code=ErrorCodes.RESOURCE_LOCKED,
            status_code=HTTPStatus.CONFLICT,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


# ============================================================================
# Workflow Exceptions
# ============================================================================

class WorkflowError(AIplatformException):
    """Base exception for workflow errors."""

    def __init__(
        self,
        message: str = "Workflow error",
        error_code: str = ErrorCodes.WORKFLOW_EXECUTION_FAILED,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow is not found."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            message=f"Workflow not found: {workflow_id}",
            error_code=ErrorCodes.WORKFLOW_NOT_FOUND,
            status_code=HTTPStatus.NOT_FOUND,
            details={"workflow_id": workflow_id},
        )


class WorkflowInvalidStateError(WorkflowError):
    """Raised when workflow is in an invalid state for the operation."""

    def __init__(
        self,
        workflow_id: str,
        current_state: str,
        expected_states: list[str],
    ) -> None:
        super().__init__(
            message=f"Workflow {workflow_id} is in invalid state '{current_state}'. "
                    f"Expected: {', '.join(expected_states)}",
            error_code=ErrorCodes.WORKFLOW_INVALID_STATE,
            status_code=HTTPStatus.CONFLICT,
            details={
                "workflow_id": workflow_id,
                "current_state": current_state,
                "expected_states": expected_states,
            },
        )


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""

    def __init__(
        self,
        workflow_id: str,
        message: str = "Workflow execution failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"workflow_id": workflow_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=message,
            error_code=ErrorCodes.WORKFLOW_EXECUTION_FAILED,
            details=error_details,
        )


class WorkflowTimeoutError(WorkflowError):
    """Raised when workflow times out."""

    def __init__(
        self,
        workflow_id: str,
        timeout_seconds: int,
    ) -> None:
        super().__init__(
            message=f"Workflow {workflow_id} timed out after {timeout_seconds} seconds",
            error_code=ErrorCodes.WORKFLOW_TIMEOUT,
            details={
                "workflow_id": workflow_id,
                "timeout_seconds": timeout_seconds,
            },
        )


class WorkflowCycleDetectedError(WorkflowError):
    """Raised when a cycle is detected in workflow DAG."""

    def __init__(self, workflow_id: str, cycle_path: list[str]) -> None:
        super().__init__(
            message=f"Cycle detected in workflow {workflow_id}",
            error_code=ErrorCodes.WORKFLOW_CYCLE_DETECTED,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={
                "workflow_id": workflow_id,
                "cycle_path": cycle_path,
            },
        )


class TaskExecutionError(WorkflowError):
    """Raised when a task execution fails."""

    def __init__(
        self,
        task_id: str,
        message: str = "Task execution failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"task_id": task_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=message,
            error_code=ErrorCodes.WORKFLOW_TASK_FAILED,
            details=error_details,
        )


# ============================================================================
# Model Exceptions
# ============================================================================

class ModelError(AIplatformException):
    """Base exception for model errors."""

    def __init__(
        self,
        message: str = "Model error",
        error_code: str = ErrorCodes.MODEL_NOT_FOUND,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class ModelNotFoundError(ModelError):
    """Raised when a model is not found."""

    def __init__(self, model_id: str) -> None:
        super().__init__(
            message=f"Model not found: {model_id}",
            error_code=ErrorCodes.MODEL_NOT_FOUND,
            status_code=HTTPStatus.NOT_FOUND,
            details={"model_id": model_id},
        )


class ModelLoadError(ModelError):
    """Raised when model loading fails."""

    def __init__(
        self,
        model_id: str,
        reason: str = "Unknown error",
    ) -> None:
        super().__init__(
            message=f"Failed to load model {model_id}: {reason}",
            error_code=ErrorCodes.MODEL_LOAD_FAILED,
            details={"model_id": model_id, "reason": reason},
        )


class ModelInferenceError(ModelError):
    """Raised when model inference fails."""

    def __init__(
        self,
        model_id: str,
        reason: str = "Unknown error",
    ) -> None:
        super().__init__(
            message=f"Model inference failed for {model_id}: {reason}",
            error_code=ErrorCodes.MODEL_INFERENCE_FAILED,
            details={"model_id": model_id, "reason": reason},
        )


class ModelInvalidFormatError(ModelError):
    """Raised when model format is invalid."""

    def __init__(
        self,
        model_id: str,
        expected_format: str,
        actual_format: str,
    ) -> None:
        super().__init__(
            message=f"Invalid model format for {model_id}. "
                    f"Expected: {expected_format}, Got: {actual_format}",
            error_code=ErrorCodes.MODEL_INVALID_FORMAT,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details={
                "model_id": model_id,
                "expected_format": expected_format,
                "actual_format": actual_format,
            },
        )


# ============================================================================
# Processing Exceptions
# ============================================================================

class ProcessingError(AIplatformException):
    """Base exception for processing errors."""

    def __init__(
        self,
        message: str = "Processing error",
        error_code: str = ErrorCodes.PROCESSING_FAILED,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class ProcessingTimeoutError(ProcessingError):
    """Raised when processing times out."""

    def __init__(
        self,
        job_id: str,
        timeout_seconds: int,
    ) -> None:
        super().__init__(
            message=f"Processing job {job_id} timed out after {timeout_seconds} seconds",
            error_code=ErrorCodes.PROCESSING_TIMEOUT,
            details={
                "job_id": job_id,
                "timeout_seconds": timeout_seconds,
            },
        )


class ResourceExhaustedError(ProcessingError):
    """Raised when processing resources are exhausted."""

    def __init__(
        self,
        resource_type: str,
        message: str = "Resource exhausted",
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCodes.PROCESSING_RESOURCE_EXHAUSTED,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details={"resource_type": resource_type},
        )


# ============================================================================
# External Service Exceptions
# ============================================================================

class ExternalServiceError(AIplatformException):
    """Base exception for external service errors."""

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        error_code: str = ErrorCodes.EXTERNAL_API_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        error_details = {"service": service_name}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"{service_name}: {message}",
            error_code=error_code,
            status_code=HTTPStatus.BAD_GATEWAY,
            details=error_details,
        )


class KafkaConnectionError(ExternalServiceError):
    """Raised when Kafka connection fails."""

    def __init__(self, message: str = "Failed to connect to Kafka") -> None:
        super().__init__(
            service_name="Kafka",
            message=message,
            error_code=ErrorCodes.KAFKA_CONNECTION_ERROR,
        )


class RedisConnectionError(ExternalServiceError):
    """Raised when Redis connection fails."""

    def __init__(self, message: str = "Failed to connect to Redis") -> None:
        super().__init__(
            service_name="Redis",
            message=message,
            error_code=ErrorCodes.REDIS_CONNECTION_ERROR,
        )


class DatabaseConnectionError(ExternalServiceError):
    """Raised when database connection fails."""

    def __init__(
        self,
        database_name: str = "Database",
        message: str = "Failed to connect to database",
    ) -> None:
        super().__init__(
            service_name=database_name,
            message=message,
            error_code=ErrorCodes.DATABASE_CONNECTION_ERROR,
        )


# ============================================================================
# Rate Limiting Exception
# ============================================================================

class RateLimitExceededError(AIplatformException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=f"Rate limit exceeded. Limit: {limit} requests per {window_seconds} seconds",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            details={
                "limit": limit,
                "window_seconds": window_seconds,
                "retry_after": retry_after,
            },
        )


# ============================================================================
# Not Implemented Exception
# ============================================================================

class NotImplementedError(AIplatformException):
    """Raised when a feature is not implemented."""

    def __init__(self, feature: str) -> None:
        super().__init__(
            message=f"Feature not implemented: {feature}",
            error_code=ErrorCodes.NOT_IMPLEMENTED,
            status_code=HTTPStatus.NOT_IMPLEMENTED,
            details={"feature": feature},
        )
