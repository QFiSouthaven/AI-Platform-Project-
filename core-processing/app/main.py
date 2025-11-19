"""
FastAPI application entry point for Core Processing module.

This module provides AI-driven code generation, debugging, and optimization
using Large Language Models from Hugging Face.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import settings
from app.kafka.consumer import KafkaConsumerService
from app.kafka.producer import KafkaProducerService
from app.models.llm_models import HealthStatus
from app.services.llm_service import LLMService

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
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global service instances
llm_service: LLMService = None
kafka_producer: KafkaProducerService = None
kafka_consumer: KafkaConsumerService = None
startup_time: float = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifespan - startup and shutdown events.
    """
    global llm_service, kafka_producer, kafka_consumer, startup_time

    startup_time = time.time()
    logger.info(
        "Starting Core Processing module",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV
    )

    # Initialize LLM service
    try:
        llm_service = LLMService()
        await llm_service.load_model()
        logger.info(
            "LLM model loaded successfully",
            model_name=settings.MODEL_NAME
        )
    except Exception as e:
        logger.error(
            "Failed to load LLM model",
            error=str(e),
            model_name=settings.MODEL_NAME
        )
        # Continue startup even if model fails to load
        llm_service = LLMService()

    # Initialize Kafka producer
    try:
        kafka_producer = KafkaProducerService()
        await kafka_producer.start()
        logger.info("Kafka producer started")
    except Exception as e:
        logger.warning(
            "Failed to start Kafka producer",
            error=str(e)
        )
        kafka_producer = None

    # Initialize Kafka consumer
    try:
        kafka_consumer = KafkaConsumerService(llm_service, kafka_producer)
        asyncio.create_task(kafka_consumer.start())
        logger.info("Kafka consumer started")
    except Exception as e:
        logger.warning(
            "Failed to start Kafka consumer",
            error=str(e)
        )
        kafka_consumer = None

    logger.info(
        "Core Processing module started successfully",
        startup_time_seconds=time.time() - startup_time
    )

    yield

    # Shutdown
    logger.info("Shutting down Core Processing module")

    if kafka_consumer:
        await kafka_consumer.stop()

    if kafka_producer:
        await kafka_producer.stop()

    if llm_service:
        await llm_service.unload_model()

    logger.info("Core Processing module shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="Core Processing Module",
    description="AI-driven code generation, debugging, and optimization using LLMs",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to requests for tracing."""
    import uuid
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    logger.info(
        "Request processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time, 2),
        correlation_id=getattr(request.state, "correlation_id", None)
    )

    return response


# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic information."""
    return {
        "service": "Core Processing Module",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the current health status of the service including
    model status, GPU availability, and Kafka connection.
    """
    global llm_service, kafka_producer, startup_time

    gpu_available = False
    gpu_memory_used = None
    gpu_memory_total = None

    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_memory_used = torch.cuda.memory_allocated() / 1024 / 1024
            gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
    except ImportError:
        pass

    model_loaded = llm_service is not None and llm_service.is_loaded
    kafka_connected = kafka_producer is not None and kafka_producer.is_connected

    uptime = time.time() - startup_time if startup_time else 0

    return HealthStatus(
        status="healthy" if model_loaded else "degraded",
        model_loaded=model_loaded,
        model_name=settings.MODEL_NAME if model_loaded else None,
        gpu_available=gpu_available,
        gpu_memory_used_mb=gpu_memory_used,
        gpu_memory_total_mb=gpu_memory_total,
        kafka_connected=kafka_connected,
        uptime_seconds=uptime,
        timestamp=datetime.utcnow()
    )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check for Kubernetes.

    Returns 200 if the service is ready to accept traffic.
    """
    global llm_service

    if llm_service is None or not llm_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: LLM model not loaded"
        )

    return {"status": "ready"}


@app.get("/live", tags=["Health"])
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Returns 200 if the service is alive.
    """
    return {"status": "alive"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        correlation_id=getattr(request.state, "correlation_id", None)
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": str(exc) if settings.DEBUG else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global llm_service
    if llm_service is None:
        raise HTTPException(
            status_code=503,
            detail="LLM service not initialized"
        )
    return llm_service


def get_kafka_producer() -> KafkaProducerService:
    """Get the global Kafka producer instance."""
    global kafka_producer
    return kafka_producer


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
