"""
FastAPI application entry point for the Workflow Orchestration module.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db, close_db
from app.api.v1 import api_router
from app.kafka.producer import get_kafka_producer, close_kafka_producer
from app.kafka.consumer import start_task_result_consumer
from app.services.scheduler import task_scheduler
from app.database import async_session_maker

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{app.version}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize Kafka producer
    try:
        producer = await get_kafka_producer()
        logger.info("Kafka producer initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Kafka producer: {e}")

    # Start Kafka consumer
    try:
        consumer = await start_task_result_consumer(async_session_maker)
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.warning(f"Failed to start Kafka consumer: {e}")

    # Start task scheduler
    try:
        task_scheduler.start()
        logger.info("Task scheduler started")
    except Exception as e:
        logger.error(f"Failed to start task scheduler: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Stop task scheduler
    task_scheduler.shutdown()

    # Close Kafka connections
    await close_kafka_producer()

    # Close database connections
    await close_db()

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Workflow Orchestration API",
    description="API for managing workflows, tasks, and executions in the AI Platform",
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


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": str(exc) if settings.DEBUG else None,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns the service status and dependencies health.
    """
    from app.models.schemas import HealthCheckResponse

    # Check dependencies
    dependencies = {}

    # Check database
    try:
        from sqlalchemy import text
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        dependencies["database"] = "healthy"
    except Exception as e:
        dependencies["database"] = f"unhealthy: {str(e)}"

    # Check Kafka
    try:
        producer = await get_kafka_producer()
        dependencies["kafka"] = "healthy" if producer._connected else "disconnected"
    except Exception as e:
        dependencies["kafka"] = f"unhealthy: {str(e)}"

    # Check scheduler
    dependencies["scheduler"] = "running" if task_scheduler.scheduler.running else "stopped"

    # Determine overall status
    status = "healthy" if all(
        "healthy" in v or "running" in v
        for v in dependencies.values()
    ) else "degraded"

    return HealthCheckResponse(
        status=status,
        service=settings.APP_NAME,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )


# Ready check endpoint
@app.get("/ready", tags=["health"])
async def ready_check():
    """
    Readiness check endpoint.

    Returns whether the service is ready to accept requests.
    """
    # Check if database is available
    try:
        from sqlalchemy import text
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": f"Database unavailable: {str(e)}"
            }
        )

    return {"status": "ready"}


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "description": "Workflow Orchestration API for the AI Platform",
        "docs": "/docs",
        "health": "/health",
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
