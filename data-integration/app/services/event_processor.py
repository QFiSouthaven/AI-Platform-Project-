"""
Event processing service for the Data Integration module.

Handles event routing, transformation, and downstream publishing.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.config import settings
from app.models.events import (
    EventMessage,
    EventMetadata,
    EventType,
    ProcessedEvent,
)

logger = structlog.get_logger(__name__)


class EventProcessor:
    """
    Processes incoming events from Kafka.

    Routes events to appropriate handlers, applies transformations,
    updates cache, and publishes downstream events.
    """

    def __init__(self, cache_manager, kafka_producer):
        """
        Initialize the event processor.

        Args:
            cache_manager: CacheManager instance for caching operations
            kafka_producer: KafkaProducerManager for publishing events
        """
        self.cache_manager = cache_manager
        self.kafka_producer = kafka_producer
        self._handlers: Dict[str, callable] = {}
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "by_type": {},
            "total_processing_time_ms": 0,
        }
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default event handlers."""
        # User events
        self.register_handler(EventType.USER_CREATED.value, self._handle_user_created)
        self.register_handler(EventType.USER_UPDATED.value, self._handle_user_updated)

        # Workflow events
        self.register_handler(EventType.TASK_COMPLETED.value, self._handle_task_completed)
        self.register_handler(EventType.TASK_FAILED.value, self._handle_task_failed)

        # Processing events
        self.register_handler(EventType.CODE_GENERATED.value, self._handle_code_generated)

        # Model events
        self.register_handler(EventType.MODEL_LOADED.value, self._handle_model_loaded)

    def register_handler(self, event_type: str, handler: callable) -> None:
        """
        Register a handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        self._handlers[event_type] = handler
        logger.info("Registered event handler", event_type=event_type)

    async def process_event(self, event: EventMessage) -> ProcessedEvent:
        """
        Process a single event.

        Args:
            event: The event to process

        Returns:
            ProcessedEvent with results
        """
        start_time = time.time()
        processed_event = ProcessedEvent(
            original_event=event,
            processing_duration_ms=0,
            transformations_applied=[],
            output_data={},
            cache_keys_updated=[],
            downstream_events=[],
            status="success",
            errors=[],
        )

        try:
            # Update stats
            self._stats["total_processed"] += 1
            event_type = event.event_type
            self._stats["by_type"][event_type] = self._stats["by_type"].get(event_type, 0) + 1

            logger.info(
                "Processing event",
                event_id=str(event.event_id),
                event_type=event_type,
                correlation_id=str(event.metadata.correlation_id),
            )

            # Find and execute handler
            handler = self._handlers.get(event_type)
            if handler:
                result = await handler(event, processed_event)
                if result:
                    processed_event.output_data.update(result)
                processed_event.transformations_applied.append(f"handler:{event_type}")
            else:
                # Default processing for unhandled events
                await self._default_handler(event, processed_event)
                processed_event.transformations_applied.append("handler:default")

            # Cache the processed event for tracing
            cache_key = f"event:{event.event_id}"
            await self.cache_manager.set(
                cache_key,
                processed_event.model_dump(),
                ttl=settings.CACHE_DEFAULT_TTL,
            )
            processed_event.cache_keys_updated.append(cache_key)

            # Publish processed event notification
            await self._publish_processed_notification(event, processed_event)

            self._stats["successful"] += 1

        except Exception as e:
            error_msg = f"Error processing event: {str(e)}"
            logger.error(
                error_msg,
                event_id=str(event.event_id),
                event_type=event.event_type,
                error=str(e),
            )
            processed_event.status = "failed"
            processed_event.errors.append(error_msg)
            self._stats["failed"] += 1

        finally:
            processing_time = (time.time() - start_time) * 1000
            processed_event.processing_duration_ms = processing_time
            self._stats["total_processing_time_ms"] += processing_time

        return processed_event

    async def _default_handler(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """
        Default handler for events without specific handlers.

        Args:
            event: The event to process
            processed_event: The processed event to update

        Returns:
            Dict with processing results
        """
        logger.debug(
            "Using default handler",
            event_type=event.event_type,
            event_id=str(event.event_id),
        )

        # Cache the raw event data
        cache_key = f"raw_event:{event.event_type}:{event.event_id}"
        await self.cache_manager.set(
            cache_key,
            event.data,
            ttl=settings.CACHE_DEFAULT_TTL,
        )
        processed_event.cache_keys_updated.append(cache_key)

        return {"processed": True, "handler": "default"}

    async def _handle_user_created(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """Handle user creation events."""
        user_data = event.data
        user_id = user_data.get("user_id") or user_data.get("id")

        if user_id:
            # Cache user data
            cache_key = f"user:{user_id}"
            await self.cache_manager.set(
                cache_key,
                user_data,
                ttl=settings.CACHE_DEFAULT_TTL * 24,  # Cache users longer
            )
            processed_event.cache_keys_updated.append(cache_key)

            # Update user count
            await self.cache_manager.increment("stats:user_count")

        logger.info("User created event processed", user_id=user_id)
        return {"user_id": user_id, "action": "created"}

    async def _handle_user_updated(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """Handle user update events."""
        user_data = event.data
        user_id = user_data.get("user_id") or user_data.get("id")

        if user_id:
            # Update cached user data
            cache_key = f"user:{user_id}"
            existing = await self.cache_manager.get(cache_key)
            if existing:
                existing.update(user_data)
                await self.cache_manager.set(
                    cache_key,
                    existing,
                    ttl=settings.CACHE_DEFAULT_TTL * 24,
                )
            else:
                await self.cache_manager.set(
                    cache_key,
                    user_data,
                    ttl=settings.CACHE_DEFAULT_TTL * 24,
                )
            processed_event.cache_keys_updated.append(cache_key)

        logger.info("User updated event processed", user_id=user_id)
        return {"user_id": user_id, "action": "updated"}

    async def _handle_task_completed(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """Handle task completion events."""
        task_data = event.data
        task_id = task_data.get("task_id")
        workflow_id = task_data.get("workflow_id")

        if task_id:
            # Cache task result
            cache_key = f"task:{task_id}:result"
            await self.cache_manager.set(
                cache_key,
                task_data,
                ttl=settings.CACHE_DEFAULT_TTL,
            )
            processed_event.cache_keys_updated.append(cache_key)

            # Update workflow progress if available
            if workflow_id:
                progress_key = f"workflow:{workflow_id}:progress"
                await self.cache_manager.increment(progress_key)

        logger.info(
            "Task completed event processed",
            task_id=task_id,
            workflow_id=workflow_id,
        )
        return {"task_id": task_id, "workflow_id": workflow_id, "status": "completed"}

    async def _handle_task_failed(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """Handle task failure events."""
        task_data = event.data
        task_id = task_data.get("task_id")
        error = task_data.get("error", "Unknown error")

        if task_id:
            # Cache task failure
            cache_key = f"task:{task_id}:error"
            await self.cache_manager.set(
                cache_key,
                {"error": error, "timestamp": datetime.now(timezone.utc).isoformat()},
                ttl=settings.CACHE_DEFAULT_TTL * 2,  # Keep errors longer
            )
            processed_event.cache_keys_updated.append(cache_key)

        logger.warning(
            "Task failed event processed",
            task_id=task_id,
            error=error,
        )
        return {"task_id": task_id, "status": "failed", "error": error}

    async def _handle_code_generated(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """Handle code generation events."""
        code_data = event.data
        request_id = code_data.get("request_id")

        if request_id:
            # Cache generated code
            cache_key = f"code:{request_id}"
            await self.cache_manager.set(
                cache_key,
                code_data,
                ttl=settings.CACHE_DEFAULT_TTL,
            )
            processed_event.cache_keys_updated.append(cache_key)

        logger.info("Code generated event processed", request_id=request_id)
        return {"request_id": request_id, "action": "code_generated"}

    async def _handle_model_loaded(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> Dict[str, Any]:
        """Handle model loaded events."""
        model_data = event.data
        model_id = model_data.get("model_id")
        model_name = model_data.get("name")

        if model_id:
            # Cache model info
            cache_key = f"model:{model_id}:info"
            await self.cache_manager.set(
                cache_key,
                model_data,
                ttl=settings.CACHE_DEFAULT_TTL * 12,  # Cache model info longer
            )
            processed_event.cache_keys_updated.append(cache_key)

            # Update loaded models list
            loaded_key = "models:loaded"
            loaded_models = await self.cache_manager.get(loaded_key) or []
            if model_id not in loaded_models:
                loaded_models.append(model_id)
                await self.cache_manager.set(
                    loaded_key,
                    loaded_models,
                    ttl=settings.CACHE_DEFAULT_TTL * 24,
                )

        logger.info(
            "Model loaded event processed",
            model_id=model_id,
            model_name=model_name,
        )
        return {"model_id": model_id, "name": model_name, "action": "loaded"}

    async def _publish_processed_notification(
        self, event: EventMessage, processed_event: ProcessedEvent
    ) -> None:
        """
        Publish notification that an event was processed.

        Args:
            event: Original event
            processed_event: Processed event result
        """
        try:
            notification = EventMessage(
                event_type=EventType.EVENT_PROCESSED.value,
                data={
                    "original_event_id": str(event.event_id),
                    "original_event_type": event.event_type,
                    "processing_duration_ms": processed_event.processing_duration_ms,
                    "status": processed_event.status,
                    "cache_keys_updated": processed_event.cache_keys_updated,
                },
                metadata=EventMetadata(
                    correlation_id=event.metadata.correlation_id,
                    source="data-integration",
                    user_id=event.metadata.user_id,
                ),
            )

            await self.kafka_producer.send(
                topic=EventType.EVENT_PROCESSED.value,
                message=notification,
            )
            processed_event.downstream_events.append(EventType.EVENT_PROCESSED.value)

        except Exception as e:
            logger.error(
                "Failed to publish processed notification",
                error=str(e),
                event_id=str(event.event_id),
            )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.

        Returns:
            Dict containing processing stats
        """
        avg_time = 0
        if self._stats["total_processed"] > 0:
            avg_time = (
                self._stats["total_processing_time_ms"]
                / self._stats["total_processed"]
            )

        return {
            "total_processed": self._stats["total_processed"],
            "successful": self._stats["successful"],
            "failed": self._stats["failed"],
            "success_rate": (
                self._stats["successful"] / self._stats["total_processed"] * 100
                if self._stats["total_processed"] > 0
                else 0
            ),
            "average_processing_time_ms": round(avg_time, 2),
            "events_by_type": self._stats["by_type"],
            "registered_handlers": list(self._handlers.keys()),
        }

    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "by_type": {},
            "total_processing_time_ms": 0,
        }
        logger.info("Event processor stats reset")
