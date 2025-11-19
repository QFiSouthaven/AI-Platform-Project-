"""
Shared logging configuration for all AI Platform modules.

This module provides a consistent logging setup across all services,
using structured JSON logging for better log aggregation and analysis.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

import structlog


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger for the given name.

    Args:
        name: The name of the logger (typically __name__).

    Returns:
        A configured structlog logger.
    """
    return structlog.get_logger(name)


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    json_logs: bool = True,
    log_to_file: bool = False,
    log_file_path: str = "app.log",
) -> None:
    """
    Configure logging for a service.

    Args:
        service_name: Name of the service for log identification.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_logs: Whether to output logs in JSON format.
        log_to_file: Whether to also log to a file.
        log_file_path: Path to the log file if log_to_file is True.
    """
    # Set the log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        add_service_name(service_name),
    ]

    if json_logs:
        # JSON output for production
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Console output for development
        shared_processors.append(structlog.dev.set_exc_info)
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    handlers: list[logging.Handler] = [console_handler]

    # File handler (optional)
    if log_to_file:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(numeric_level)
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)


def add_service_name(service_name: str):
    """
    Processor to add service name to log entries.

    Args:
        service_name: Name of the service.

    Returns:
        A structlog processor function.
    """
    def processor(
        logger: logging.Logger,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        event_dict["service"] = service_name
        return event_dict

    return processor


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter to add correlation ID to log records.
    """

    def __init__(self, correlation_id: str = "") -> None:
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.correlation_id  # type: ignore
        return True


def bind_correlation_id(correlation_id: str) -> None:
    """
    Bind a correlation ID to the current context for all subsequent logs.

    Args:
        correlation_id: The correlation ID to bind.
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_correlation_id() -> None:
    """
    Clear the correlation ID from the current context.
    """
    structlog.contextvars.unbind_contextvars("correlation_id")


def log_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """
    Log an HTTP request with standard fields.

    Args:
        logger: The logger to use.
        method: HTTP method.
        path: Request path.
        status_code: Response status code.
        duration_ms: Request duration in milliseconds.
        user_id: Optional user ID.
        correlation_id: Optional correlation ID.
    """
    logger.info(
        "HTTP request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        user_id=user_id,
        correlation_id=correlation_id,
    )


def log_kafka_message(
    logger: structlog.stdlib.BoundLogger,
    topic: str,
    event_type: str,
    direction: str,
    correlation_id: str | None = None,
    partition: int | None = None,
    offset: int | None = None,
) -> None:
    """
    Log a Kafka message with standard fields.

    Args:
        logger: The logger to use.
        topic: Kafka topic.
        event_type: Type of the event.
        direction: 'produced' or 'consumed'.
        correlation_id: Optional correlation ID.
        partition: Optional partition number.
        offset: Optional message offset.
    """
    logger.info(
        f"Kafka message {direction}",
        topic=topic,
        event_type=event_type,
        direction=direction,
        correlation_id=correlation_id,
        partition=partition,
        offset=offset,
    )


def log_database_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    table: str,
    duration_ms: float,
    rows_affected: int | None = None,
    success: bool = True,
) -> None:
    """
    Log a database operation with standard fields.

    Args:
        logger: The logger to use.
        operation: Type of operation (SELECT, INSERT, UPDATE, DELETE).
        table: Database table name.
        duration_ms: Operation duration in milliseconds.
        rows_affected: Number of rows affected.
        success: Whether the operation was successful.
    """
    log_method = logger.info if success else logger.error
    log_method(
        "Database operation",
        operation=operation,
        table=table,
        duration_ms=round(duration_ms, 2),
        rows_affected=rows_affected,
        success=success,
    )


# Example usage and module initialization
if __name__ == "__main__":
    # Example configuration
    configure_logging(
        service_name="example-service",
        log_level="DEBUG",
        json_logs=False,  # Use False for development
    )

    # Get a logger
    logger = get_logger(__name__)

    # Log some messages
    logger.info("Service started", version="1.0.0")
    logger.debug("Debug message", extra_data={"key": "value"})
    logger.warning("Warning message")

    # With correlation ID
    bind_correlation_id("test-correlation-123")
    logger.info("Request processed", user_id="user123")
    clear_correlation_id()

    # Log HTTP request
    log_request(
        logger,
        method="GET",
        path="/api/v1/users",
        status_code=200,
        duration_ms=45.5,
        user_id="user123",
    )
