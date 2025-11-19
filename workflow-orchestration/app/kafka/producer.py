"""
Kafka producer for publishing workflow and task events.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional
import uuid

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Async Kafka producer for workflow events."""

    def __init__(self):
        """Initialize Kafka producer."""
        self._producer: Optional[AIOKafkaProducer] = None
        self._connected = False

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._connected:
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                enable_idempotence=True,
                max_batch_size=16384,
                linger_ms=10,
            )
            await self._producer.start()
            self._connected = True
            logger.info("Kafka producer started successfully")
        except KafkaError as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer and self._connected:
            await self._producer.stop()
            self._connected = False
            logger.info("Kafka producer stopped")

    async def _publish(
        self,
        topic: str,
        message: dict[str, Any],
        key: Optional[str] = None
    ) -> None:
        """
        Publish a message to a Kafka topic.

        Args:
            topic: Kafka topic
            message: Message payload
            key: Optional message key for partitioning
        """
        if not self._connected:
            logger.warning("Kafka producer not connected, attempting to reconnect")
            await self.start()

        try:
            await self._producer.send_and_wait(topic, value=message, key=key)
            logger.debug(
                f"Published message to {topic}",
                extra={"topic": topic, "key": key}
            )
        except KafkaError as e:
            logger.error(f"Failed to publish message to {topic}: {e}")
            raise

    def _create_event_message(
        self,
        event_type: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Create a standardized event message.

        Args:
            event_type: Type of event
            data: Event data
            correlation_id: Optional correlation ID for tracing

        Returns:
            Formatted event message
        """
        return {
            "schema_version": "1.0",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": {
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "source": "workflow-orchestration",
            }
        }

    async def publish_workflow_event(
        self,
        event_type: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish a workflow event.

        Args:
            event_type: Type of workflow event
            data: Event data
            correlation_id: Optional correlation ID
        """
        message = self._create_event_message(event_type, data, correlation_id)
        key = str(data.get("workflow_id", ""))

        await self._publish(
            settings.KAFKA_WORKFLOW_EVENTS_TOPIC,
            message,
            key
        )

        logger.info(
            f"Published workflow event: {event_type}",
            extra={
                "event_type": event_type,
                "workflow_id": data.get("workflow_id"),
                "execution_id": data.get("execution_id"),
                "correlation_id": message["metadata"]["correlation_id"]
            }
        )

    async def publish_task_event(
        self,
        event_type: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish a task event.

        Args:
            event_type: Type of task event
            data: Event data
            correlation_id: Optional correlation ID
        """
        message = self._create_event_message(event_type, data, correlation_id)
        key = str(data.get("task_id", ""))

        await self._publish(
            settings.KAFKA_TASK_EVENTS_TOPIC,
            message,
            key
        )

        logger.info(
            f"Published task event: {event_type}",
            extra={
                "event_type": event_type,
                "task_id": data.get("task_id"),
                "task_execution_id": data.get("task_execution_id"),
                "correlation_id": message["metadata"]["correlation_id"]
            }
        )

    async def publish_task_result(
        self,
        task_execution_id: int,
        task_id: int,
        workflow_execution_id: int,
        status: str,
        output_data: dict[str, Any],
        error_message: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish a task execution result.

        Args:
            task_execution_id: Task execution ID
            task_id: Task ID
            workflow_execution_id: Workflow execution ID
            status: Task status
            output_data: Task output
            error_message: Optional error message
            correlation_id: Optional correlation ID
        """
        data = {
            "task_execution_id": task_execution_id,
            "task_id": task_id,
            "workflow_execution_id": workflow_execution_id,
            "status": status,
            "output_data": output_data,
            "error_message": error_message,
        }

        message = self._create_event_message("task.result", data, correlation_id)

        await self._publish(
            settings.KAFKA_TASK_RESULTS_TOPIC,
            message,
            str(workflow_execution_id)
        )

        logger.info(
            f"Published task result",
            extra={
                "task_execution_id": task_execution_id,
                "status": status,
                "correlation_id": message["metadata"]["correlation_id"]
            }
        )


# Global producer instance
_kafka_producer: Optional[KafkaProducer] = None


async def get_kafka_producer() -> KafkaProducer:
    """
    Get the global Kafka producer instance.

    Returns:
        KafkaProducer: Kafka producer instance
    """
    global _kafka_producer

    if _kafka_producer is None:
        _kafka_producer = KafkaProducer()

    if not _kafka_producer._connected:
        try:
            await _kafka_producer.start()
        except Exception as e:
            logger.warning(f"Could not connect to Kafka: {e}")
            # Return producer anyway for graceful degradation

    return _kafka_producer


async def close_kafka_producer() -> None:
    """Close the global Kafka producer."""
    global _kafka_producer

    if _kafka_producer:
        await _kafka_producer.stop()
        _kafka_producer = None
