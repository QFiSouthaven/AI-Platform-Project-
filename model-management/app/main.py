"""
Main FastAPI application for Model Management module.

Entry point for the Model Management service with plugin loading on startup.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import get_settings
from app.database import Database
from app.services.plugin_service import PluginService
from app.utils.encryption import encryption_service
from app.utils.storage import storage_service

settings = get_settings()

# Configure structured logging
def configure_logging():
    """Configure structured logging with JSON output."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Model Management service", app_name=settings.APP_NAME)

    # Connect to database
    await Database.connect()
    logger.info("Database connected")

    # Initialize storage service
    await storage_service.initialize()
    logger.info("Storage service initialized")

    # Initialize encryption service
    if settings.ENABLE_ENCRYPTION:
        await encryption_service.initialize()
        logger.info("Encryption service initialized")

    # Load active plugins
    try:
        db = Database.get_db()
        plugin_service = PluginService(db)
        loaded_count = await plugin_service.load_all_active_plugins()
        logger.info("Active plugins loaded", count=loaded_count)
    except Exception as e:
        logger.warning("Failed to load plugins on startup", error=str(e))

    logger.info(
        "Model Management service started",
        host=settings.HOST,
        port=settings.PORT,
        environment=settings.APP_ENV,
    )

    yield

    # Shutdown
    logger.info("Shutting down Model Management service")

    # Disconnect from database
    await Database.disconnect()
    logger.info("Database disconnected")

    logger.info("Model Management service stopped")


# Create FastAPI application
app = FastAPI(
    title="Model Management API",
    description="AI Platform Model Management service for storing, loading, and managing AI models with plugin support.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns service health status and component information.
    """
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
    }

    # Check database
    try:
        db = Database.get_db()
        await db.command("ping")
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check encryption service
    if settings.ENABLE_ENCRYPTION:
        try:
            key_info = await encryption_service.get_key_info()
            health_status["components"]["encryption"] = {
                "status": key_info.get("status", "unknown"),
                "key_count": key_info.get("key_count", 0),
            }
        except Exception as e:
            health_status["components"]["encryption"] = {
                "status": "unhealthy",
                "error": str(e),
            }

    # Check storage
    try:
        storage_stats = await storage_service.get_storage_stats()
        health_status["components"]["storage"] = {
            "status": "healthy",
            "disk_free_gb": round(storage_stats["disk_free_bytes"] / (1024**3), 2),
        }
    except Exception as e:
        health_status["components"]["storage"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    return health_status


# Ready check endpoint
@app.get("/ready", tags=["health"])
async def ready_check() -> Dict[str, str]:
    """
    Readiness check endpoint.

    Returns whether the service is ready to accept traffic.
    """
    try:
        # Verify database connection
        db = Database.get_db()
        await db.command("ping")

        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


# Info endpoint
@app.get("/info", tags=["health"])
async def info() -> Dict[str, Any]:
    """
    Get service information.
    """
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "api_version": "v1",
        "docs_url": "/docs",
        "health_url": "/health",
    }


# Storage stats endpoint
@app.get("/storage/stats", tags=["storage"])
async def get_storage_stats() -> Dict[str, Any]:
    """
    Get storage usage statistics.
    """
    stats = await storage_service.get_storage_stats()

    return {
        "model_storage_mb": round(stats["model_storage_bytes"] / (1024**2), 2),
        "plugin_storage_mb": round(stats["plugin_storage_bytes"] / (1024**2), 2),
        "temp_storage_mb": round(stats["temp_storage_bytes"] / (1024**2), 2),
        "total_used_mb": round(stats["total_used_bytes"] / (1024**2), 2),
        "disk_total_gb": round(stats["disk_total_bytes"] / (1024**3), 2),
        "disk_used_gb": round(stats["disk_used_bytes"] / (1024**3), 2),
        "disk_free_gb": round(stats["disk_free_bytes"] / (1024**3), 2),
    }


# Cleanup endpoint
@app.post("/storage/cleanup", tags=["storage"])
async def cleanup_temp_files(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old temporary files.
    """
    deleted_count = await storage_service.cleanup_temp_files(max_age_hours)
    return {
        "status": "success",
        "deleted_files": deleted_count,
        "max_age_hours": max_age_hours,
    }


# Encryption key info endpoint
@app.get("/encryption/info", tags=["encryption"])
async def get_encryption_info() -> Dict[str, Any]:
    """
    Get encryption key information.
    """
    if not settings.ENABLE_ENCRYPTION:
        return {"status": "disabled", "message": "Encryption is disabled"}

    return await encryption_service.get_key_info()


# Key rotation endpoint
@app.post("/encryption/rotate", tags=["encryption"])
async def rotate_encryption_key() -> Dict[str, Any]:
    """
    Rotate encryption key.

    Generates a new primary encryption key.
    """
    if not settings.ENABLE_ENCRYPTION:
        raise HTTPException(status_code=400, detail="Encryption is disabled")

    key_id = await encryption_service.rotate_key()
    return {
        "status": "success",
        "message": "Encryption key rotated",
        "new_key_id": key_id,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )
