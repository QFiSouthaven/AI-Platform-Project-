"""
Main FastAPI application for User Gateway module.

Entry point for the User Gateway service, providing authentication,
API routing, and event publishing functionality.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.api.v1.routes import router as users_router
from app.api.v1.auth import router as auth_router
from app.kafka.publisher import get_kafka_publisher


def setup_logging() -> None:
    """Configure structured JSON logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    logger = structlog.get_logger()

    # Startup
    logger.info(
        "Starting User Gateway",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )

    # Initialize database
    await init_db()

    # Initialize Kafka publisher
    kafka_publisher = get_kafka_publisher()
    await kafka_publisher.start()

    yield

    # Shutdown
    logger.info("Shutting down User Gateway")

    # Close Kafka publisher
    await kafka_publisher.stop()

    # Close database connections
    await close_db()


# Setup logging before app creation
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="User Gateway API",
    description="Entry point for all user interactions with the AI Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger = structlog.get_logger()
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle general exceptions."""
    logger = structlog.get_logger()
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": str(exc) if settings.DEBUG else None,
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Include API routers
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
)

app.include_router(
    users_router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"],
)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint.

    Returns:
        dict: Welcome message and API information.
    """
    return {
        "status": "success",
        "message": "Welcome to User Gateway API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        dict: Health status of the service.
    """
    return {
        "status": "success",
        "data": {
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "healthy": True,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.

    Returns:
        dict: Readiness status of the service.
    """
    # TODO: Add database and Kafka connectivity checks
    return {
        "status": "success",
        "data": {
            "service": settings.APP_NAME,
            "ready": True,
            "checks": {
                "database": "ok",
                "kafka": "ok",
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
