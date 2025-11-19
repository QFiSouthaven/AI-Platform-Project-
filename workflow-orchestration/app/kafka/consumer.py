"""
Kafka consumer for receiving task results and events.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.config import settings

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Async Kafka consumer for task results and events."""

    def __init__(self):
        """Initialize Kafka consumer."""
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._handlers: dict[str, Callable] = {}

    async def start(self, topics: list[str]) -> None:
        """
        Start the Kafka consumer.

        Args:
            topics: List of topics to subscribe to
        """
        try:
            self._consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            )
            await self._consumer.start()
            self._running = True
            logger.info(f"Kafka consumer started, subscribed to: {topics}")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], None]
    ) -> None:
        """
        Register a handler for an event type.

        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def consume(self) -> None:
        """
        Start consuming messages.

        This is a blocking operation that runs until stopped.
        """
        if not self._consumer:
            raise RuntimeError("Consumer not started")

        logger.info("Starting message consumption")

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(
                        f"Error processing message: {e}",
                        extra={
                            "topic": message.topic,
                            "partition": message.partition,
                            "offset": message.offset,
                        }
                    )
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise

    async def _process_message(self, message) -> None:
        """
        Process a received message.

        Args:
            message: Kafka message
        """
        value = message.value
        event_type = value.get("event_type")

        logger.debug(
            f"Received message",
            extra={
                "topic": message.topic,
                "event_type": event_type,
                "correlation_id": value.get("metadata", {}).get("correlation_id"),
            }
        )

        # Find and call handler
        handler = self._handlers.get(event_type)
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(value)
                else:
                    handler(value)
            except Exception as e:
                logger.error(
                    f"Handler error for {event_type}: {e}",
                    extra={"event_type": event_type}
                )
        else:
            logger.warning(f"No handler registered for event type: {event_type}")


class TaskResultConsumer(KafkaConsumer):
    """Specialized consumer for task results."""

    def __init__(self, db_session_factory):
        """
        Initialize task result consumer.

        Args:
            db_session_factory: Factory for creating database sessions
        """
        super().__init__()
        self.db_session_factory = db_session_factory
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up event handlers."""
        self.register_handler("task.result", self._handle_task_result)
        self.register_handler("task.started", self._handle_task_started)
        self.register_handler("task.completed", self._handle_task_completed)
        self.register_handler("task.failed", self._handle_task_failed)

    async def _handle_task_result(self, message: dict[str, Any]) -> None:
        """
        Handle task result event.

        Args:
            message: Event message
        """
        data = message.get("data", {})
        task_execution_id = data.get("task_execution_id")
        status = data.get("status")
        output_data = data.get("output_data", {})
        error_message = data.get("error_message")

        logger.info(
            f"Handling task result",
            extra={
                "task_execution_id": task_execution_id,
                "status": status,
            }
        )

        async with self.db_session_factory() as db:
            from app.services.task_service import TaskService
            from app.models.task import TaskStatus

            service = TaskService(db)
            status_enum = TaskStatus(status)

            await service.update_task_execution_status(
                task_execution_id,
                status_enum,
                error_message=error_message,
                output_data=output_data
            )

    async def _handle_task_started(self, message: dict[str, Any]) -> None:
        """
        Handle task started event.

        Args:
            message: Event message
        """
        data = message.get("data", {})
        logger.info(
            f"Task started",
            extra={
                "task_id": data.get("task_id"),
                "task_execution_id": data.get("task_execution_id"),
            }
        )

    async def _handle_task_completed(self, message: dict[str, Any]) -> None:
        """
        Handle task completed event.

        Args:
            message: Event message
        """
        data = message.get("data", {})
        logger.info(
            f"Task completed",
            extra={
                "task_id": data.get("task_id"),
                "task_execution_id": data.get("task_execution_id"),
            }
        )

    async def _handle_task_failed(self, message: dict[str, Any]) -> None:
        """
        Handle task failed event.

        Args:
            message: Event message
        """
        data = message.get("data", {})
        logger.warning(
            f"Task failed",
            extra={
                "task_id": data.get("task_id"),
                "task_execution_id": data.get("task_execution_id"),
                "error": data.get("error"),
            }
        )


async def start_task_result_consumer(db_session_factory) -> TaskResultConsumer:
    """
    Start the task result consumer.

    Args:
        db_session_factory: Factory for creating database sessions

    Returns:
        TaskResultConsumer: Started consumer instance
    """
    consumer = TaskResultConsumer(db_session_factory)

    await consumer.start([
        settings.KAFKA_TASK_RESULTS_TOPIC,
        settings.KAFKA_TASK_EVENTS_TOPIC,
    ])

    # Start consuming in background
    asyncio.create_task(consumer.consume())

    return consumer
