"""
FastAPI application entry point for the Data Integration module.

Provides event-driven communication, caching, and application assembly
capabilities for the AI Platform.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.cache.redis_client import RedisClient
from app.cache.cache_manager import CacheManager
from app.config import settings
from app.kafka.consumer import KafkaConsumerManager
from app.kafka.producer import KafkaProducerManager
from app.services.event_processor import EventProcessor


# Configure structured logging
def configure_logging() -> None:
    """Configure structured JSON logging."""
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

    # Set log level
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )


configure_logging()
logger = structlog.get_logger(__name__)

# Global instances
redis_client: RedisClient = None
cache_manager: CacheManager = None
kafka_producer: KafkaProducerManager = None
kafka_consumer: KafkaConsumerManager = None
event_processor: EventProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown of background services.
    """
    global redis_client, cache_manager, kafka_producer, kafka_consumer, event_processor

    logger.info(
        "Starting Data Integration module",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )

    try:
        # Initialize Redis client
        redis_client = RedisClient()
        await redis_client.connect()
        logger.info("Redis client connected", redis_url=settings.REDIS_URL)

        # Initialize cache manager
        cache_manager = CacheManager(redis_client)
        app.state.cache_manager = cache_manager

        # Initialize Kafka producer
        kafka_producer = KafkaProducerManager()
        await kafka_producer.start()
        logger.info(
            "Kafka producer started",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        app.state.kafka_producer = kafka_producer

        # Initialize event processor
        event_processor = EventProcessor(cache_manager, kafka_producer)
        app.state.event_processor = event_processor

        # Initialize and start Kafka consumer
        kafka_consumer = KafkaConsumerManager(
            topics=settings.KAFKA_CONSUME_TOPICS,
            event_processor=event_processor,
        )

        # Start consumer in background
        consumer_task = asyncio.create_task(kafka_consumer.start())
        logger.info(
            "Kafka consumer started",
            topics=settings.KAFKA_CONSUME_TOPICS,
            group_id=settings.KAFKA_GROUP_ID,
        )

        yield

        # Shutdown
        logger.info("Shutting down Data Integration module")

        # Stop Kafka consumer
        if kafka_consumer:
            await kafka_consumer.stop()
            logger.info("Kafka consumer stopped")

        # Stop Kafka producer
        if kafka_producer:
            await kafka_producer.stop()
            logger.info("Kafka producer stopped")

        # Close Redis connection
        if redis_client:
            await redis_client.disconnect()
            logger.info("Redis client disconnected")

    except Exception as e:
        logger.error("Error during application lifecycle", error=str(e))
        raise


# Create FastAPI application
app = FastAPI(
    title="Data Integration Module",
    description="Event-driven communication, caching, and application assembly for AI Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.now(timezone.utc)

    response = await call_next(request)

    process_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time, 2),
    )

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions."""
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
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.DEBUG else {},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Dict containing health status and component states
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": settings.APP_NAME,
        "version": "1.0.0",
        "components": {},
    }

    # Check Redis
    try:
        if redis_client and await redis_client.ping():
            health_status["components"]["redis"] = "healthy"
        else:
            health_status["components"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Kafka producer
    try:
        if kafka_producer and kafka_producer.is_connected():
            health_status["components"]["kafka_producer"] = "healthy"
        else:
            health_status["components"]["kafka_producer"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["kafka_producer"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Kafka consumer
    try:
        if kafka_consumer and kafka_consumer.is_running():
            health_status["components"]["kafka_consumer"] = "healthy"
        else:
            health_status["components"]["kafka_consumer"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["kafka_consumer"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@app.get("/ready", tags=["health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes.

    Returns:
        Dict containing readiness status
    """
    is_ready = True
    details = {}

    # Check if Redis is ready
    try:
        if redis_client:
            await redis_client.ping()
            details["redis"] = "ready"
        else:
            details["redis"] = "not initialized"
            is_ready = False
    except Exception as e:
        details["redis"] = f"not ready: {str(e)}"
        is_ready = False

    # Check if Kafka producer is ready
    if kafka_producer and kafka_producer.is_connected():
        details["kafka_producer"] = "ready"
    else:
        details["kafka_producer"] = "not ready"
        is_ready = False

    return {
        "status": "ready" if is_ready else "not ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }


@app.get("/metrics", tags=["monitoring"])
async def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics.

    Returns:
        Dict containing application metrics
    """
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": settings.APP_NAME,
    }

    # Get cache stats if available
    if cache_manager:
        try:
            cache_stats = await cache_manager.get_stats()
            metrics["cache"] = cache_stats
        except Exception as e:
            metrics["cache"] = {"error": str(e)}

    # Get event processor stats if available
    if event_processor:
        try:
            processor_stats = event_processor.get_stats()
            metrics["event_processor"] = processor_stats
        except Exception as e:
            metrics["event_processor"] = {"error": str(e)}

    return metrics


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
