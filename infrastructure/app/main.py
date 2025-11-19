"""
Infrastructure Module - FastAPI Application Entry Point

This module initializes the FastAPI application with Ray cluster integration,
providing distributed task execution and resource management capabilities.
Windows 11 compatible implementation.
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog

# Windows event loop policy for asyncio compatibility
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.ray_service import RayService
from app.services.health_monitor import HealthMonitor
from app.services.autoscaler import AutoScaler
from app.services.resource_manager import ResourceManager
from app.api.v1 import tasks, workers, metrics, scaling

# Configure structured logging
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
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Infrastructure Module", version=settings.APP_VERSION)

    try:
        # Initialize Ray service
        app.state.ray_service = RayService()
        await app.state.ray_service.initialize()
        logger.info("Ray service initialized successfully")

        # Initialize Resource Manager
        app.state.resource_manager = ResourceManager()
        await app.state.resource_manager.initialize()
        logger.info("Resource manager initialized")

        # Initialize Health Monitor
        app.state.health_monitor = HealthMonitor(
            ray_service=app.state.ray_service,
            resource_manager=app.state.resource_manager
        )
        await app.state.health_monitor.start()
        logger.info("Health monitor started")

        # Initialize AutoScaler
        app.state.autoscaler = AutoScaler(
            ray_service=app.state.ray_service,
            resource_manager=app.state.resource_manager,
            health_monitor=app.state.health_monitor
        )
        await app.state.autoscaler.start()
        logger.info("AutoScaler started")

        logger.info("Infrastructure Module started successfully")

    except Exception as e:
        logger.error("Failed to start Infrastructure Module", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Infrastructure Module")

    try:
        await app.state.autoscaler.stop()
        await app.state.health_monitor.stop()
        await app.state.resource_manager.cleanup()
        await app.state.ray_service.shutdown()
        logger.info("Infrastructure Module shut down successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Infrastructure Module for distributed computing and resource management",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for tracing."""
    import uuid
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        "Unhandled exception",
        error=str(exc),
        correlation_id=correlation_id,
        path=request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"correlation_id": correlation_id}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include API routers
app.include_router(
    tasks.router,
    prefix="/api/v1/tasks",
    tags=["tasks"]
)

app.include_router(
    workers.router,
    prefix="/api/v1/workers",
    tags=["workers"]
)

app.include_router(
    metrics.router,
    prefix="/api/v1/metrics",
    tags=["metrics"]
)

app.include_router(
    scaling.router,
    prefix="/api/v1/scaling",
    tags=["scaling"]
)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "status": "success",
        "data": {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for load balancer and Kubernetes probes.
    """
    try:
        ray_service = request.app.state.ray_service
        health_monitor = request.app.state.health_monitor

        ray_healthy = await ray_service.is_healthy()
        cluster_status = await health_monitor.get_cluster_health()

        is_healthy = ray_healthy and cluster_status.get("status") == "healthy"

        return {
            "status": "success" if is_healthy else "degraded",
            "data": {
                "service": "healthy" if is_healthy else "unhealthy",
                "ray_cluster": "connected" if ray_healthy else "disconnected",
                "cluster_health": cluster_status,
                "uptime_seconds": health_monitor.get_uptime()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "data": {
                    "service": "unhealthy",
                    "error": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/ready")
async def readiness_check(request: Request):
    """
    Readiness check for Kubernetes.
    """
    try:
        ray_service = request.app.state.ray_service
        is_ready = await ray_service.is_ready()

        if is_ready:
            return {
                "status": "success",
                "data": {"ready": True},
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "data": {"ready": False},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "data": {"ready": False, "error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
