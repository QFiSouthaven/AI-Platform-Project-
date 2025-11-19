"""
Event management API endpoints for the Data Integration module.

Provides endpoints for publishing, querying, and managing events.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import settings
from app.models.events import (
    EventBatchRequest,
    EventBatchResponse,
    EventMessage,
    EventMetadata,
    EventPublishRequest,
    EventPublishResponse,
    EventQueryRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_event_processor(request: Request):
    """Get event processor from app state."""
    return request.app.state.event_processor


def get_kafka_producer(request: Request):
    """Get Kafka producer from app state."""
    return request.app.state.kafka_producer


def get_cache_manager(request: Request):
    """Get cache manager from app state."""
    return request.app.state.cache_manager


@router.post("/publish", response_model=EventPublishResponse)
async def publish_event(
    event_request: EventPublishRequest,
    request: Request,
    kafka_producer=Depends(get_kafka_producer),
) -> EventPublishResponse:
    """
    Publish an event to Kafka.

    Args:
        event_request: Event data to publish
        request: FastAPI request
        kafka_producer: Kafka producer instance

    Returns:
        EventPublishResponse with publish status
    """
    try:
        # Create event message
        event = EventMessage(
            event_type=event_request.event_type,
            data=event_request.data,
            metadata=EventMetadata(
                correlation_id=event_request.correlation_id or uuid4(),
                source="data-integration-api",
                priority=event_request.priority,
            ),
        )

        # Determine topic
        topic = event_request.topic or event_request.event_type

        # Publish to Kafka
        result = await kafka_producer.send(
            topic=topic,
            message=event,
            key=event_request.partition_key,
        )

        logger.info(
            "Event published",
            event_id=str(event.event_id),
            event_type=event_request.event_type,
            topic=topic,
        )

        return EventPublishResponse(
            status="success",
            event_id=event.event_id,
            topic=topic,
            partition=result.get("partition"),
            offset=result.get("offset"),
            timestamp=datetime.now(timezone.utc),
            message="Event published successfully",
        )

    except Exception as e:
        logger.error("Failed to publish event", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")


@router.post("/publish/batch", response_model=EventBatchResponse)
async def publish_batch_events(
    batch_request: EventBatchRequest,
    request: Request,
    kafka_producer=Depends(get_kafka_producer),
) -> EventBatchResponse:
    """
    Publish multiple events in a batch.

    Args:
        batch_request: Batch of events to publish
        request: FastAPI request
        kafka_producer: Kafka producer instance

    Returns:
        EventBatchResponse with batch results
    """
    results = []
    errors = []
    successful = 0
    failed = 0

    for i, event_request in enumerate(batch_request.events):
        try:
            # Create event message
            event = EventMessage(
                event_type=event_request.event_type,
                data=event_request.data,
                metadata=EventMetadata(
                    correlation_id=event_request.correlation_id or uuid4(),
                    source="data-integration-api",
                    priority=event_request.priority,
                ),
            )

            # Determine topic
            topic = event_request.topic or event_request.event_type

            # Publish to Kafka
            result = await kafka_producer.send(
                topic=topic,
                message=event,
                key=event_request.partition_key,
            )

            results.append(
                EventPublishResponse(
                    status="success",
                    event_id=event.event_id,
                    topic=topic,
                    partition=result.get("partition"),
                    offset=result.get("offset"),
                    timestamp=datetime.now(timezone.utc),
                    message="Event published successfully",
                )
            )
            successful += 1

        except Exception as e:
            error_detail = {
                "index": i,
                "event_type": event_request.event_type,
                "error": str(e),
            }
            errors.append(error_detail)
            failed += 1

            if batch_request.fail_on_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Batch failed at index {i}: {str(e)}",
                )

            # Add failed result
            results.append(
                EventPublishResponse(
                    status="failed",
                    event_id=uuid4(),
                    topic=event_request.topic or event_request.event_type,
                    timestamp=datetime.now(timezone.utc),
                    message=f"Failed: {str(e)}",
                )
            )

    return EventBatchResponse(
        status="success" if failed == 0 else "partial" if successful > 0 else "failed",
        total=len(batch_request.events),
        successful=successful,
        failed=failed,
        results=results,
        errors=errors,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: UUID,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    Get a processed event by ID.

    Args:
        event_id: UUID of the event
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        Event data if found
    """
    cache_key = f"event:{event_id}"
    event_data = await cache_manager.get(cache_key)

    if not event_data:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    return {
        "status": "success",
        "data": event_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/", response_model=Dict[str, Any])
async def list_events(
    request: Request,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum events to return"),
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    List recent events from cache.

    Args:
        request: FastAPI request
        event_type: Optional event type filter
        limit: Maximum number of events
        cache_manager: Cache manager instance

    Returns:
        List of events
    """
    try:
        # Get events from cache using pattern
        pattern = f"event:*" if not event_type else f"raw_event:{event_type}:*"
        keys = await cache_manager.get_keys(pattern, limit=limit)

        events = []
        for key in keys:
            event_data = await cache_manager.get(key)
            if event_data:
                events.append({
                    "key": key,
                    "data": event_data,
                })

        return {
            "status": "success",
            "data": events,
            "count": len(events),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to list events", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_event_stats(
    request: Request,
    event_processor=Depends(get_event_processor),
) -> Dict[str, Any]:
    """
    Get event processing statistics.

    Args:
        request: FastAPI request
        event_processor: Event processor instance

    Returns:
        Event processing statistics
    """
    stats = event_processor.get_stats()

    return {
        "status": "success",
        "data": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/stats/reset", response_model=Dict[str, Any])
async def reset_event_stats(
    request: Request,
    event_processor=Depends(get_event_processor),
) -> Dict[str, Any]:
    """
    Reset event processing statistics.

    Args:
        request: FastAPI request
        event_processor: Event processor instance

    Returns:
        Confirmation message
    """
    event_processor.reset_stats()

    return {
        "status": "success",
        "message": "Event statistics reset successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/types", response_model=Dict[str, Any])
async def list_event_types(
    request: Request,
) -> Dict[str, Any]:
    """
    List all available event types.

    Args:
        request: FastAPI request

    Returns:
        List of event types
    """
    from app.models.events import EventType

    event_types = [
        {
            "name": et.name,
            "value": et.value,
        }
        for et in EventType
    ]

    return {
        "status": "success",
        "data": event_types,
        "count": len(event_types),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/{event_id}", response_model=Dict[str, Any])
async def delete_event(
    event_id: UUID,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    Delete a cached event by ID.

    Args:
        event_id: UUID of the event
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        Deletion confirmation
    """
    cache_key = f"event:{event_id}"
    deleted = await cache_manager.delete(cache_key)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    return {
        "status": "success",
        "message": f"Event {event_id} deleted successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
