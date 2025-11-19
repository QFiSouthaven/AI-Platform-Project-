"""
Kafka publisher for User Gateway.

Provides async Kafka producer for publishing events to Kafka topics.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.config import settings

logger = logging.getLogger(__name__)


class KafkaPublisher:
    """
    Async Kafka publisher for publishing events.

    Implements the singleton pattern to ensure a single producer instance.
    """

    _instance: Optional["KafkaPublisher"] = None
    _producer: Optional[AIOKafkaProducer] = None

    def __new__(cls) -> "KafkaPublisher":
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def start(self) -> None:
        """
        Start the Kafka producer.

        Should be called on application startup.
        """
        if self._producer is not None:
            logger.warning("Kafka producer is already running")
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                enable_idempotence=True,
                max_batch_size=16384,
                linger_ms=10,
                compression_type="gzip",
            )
            await self._producer.start()
            logger.info(
                f"Kafka producer started, connected to {settings.KAFKA_BOOTSTRAP_SERVERS}"
            )
        except KafkaError as e:
            logger.error(f"Failed to start Kafka producer: {str(e)}")
            self._producer = None
            raise

    async def stop(self) -> None:
        """
        Stop the Kafka producer.

        Should be called on application shutdown.
        """
        if self._producer is None:
            logger.warning("Kafka producer is not running")
            return

        try:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")
        except KafkaError as e:
            logger.error(f"Error stopping Kafka producer: {str(e)}")
            raise

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None,
    ) -> bool:
        """
        Publish a message to a Kafka topic.

        Args:
            topic: Topic name to publish to.
            message: Message data to publish.
            key: Optional message key for partitioning.

        Returns:
            bool: True if message was published successfully, False otherwise.
        """
        if self._producer is None:
            logger.error("Kafka producer is not initialized")
            return False

        try:
            # Add topic prefix if configured
            full_topic = topic
            if settings.KAFKA_TOPIC_PREFIX and not topic.startswith(
                settings.KAFKA_TOPIC_PREFIX
            ):
                full_topic = f"{settings.KAFKA_TOPIC_PREFIX}.{topic}"

            # Send message
            result = await self._producer.send_and_wait(
                full_topic,
                value=message,
                key=key,
            )

            logger.debug(
                f"Message published to {full_topic}",
                extra={
                    "topic": full_topic,
                    "partition": result.partition,
                    "offset": result.offset,
                },
            )
            return True

        except KafkaError as e:
            logger.error(
                f"Failed to publish message to {topic}: {str(e)}",
                extra={"topic": topic, "error": str(e)},
            )
            return False

    async def publish_event(
        self,
        topic: str,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publish a structured event to a Kafka topic.

        Wraps the data in a standard event envelope with metadata.

        Args:
            topic: Topic name to publish to.
            event_type: Type of event (e.g., "user.created").
            data: Event data payload.
            correlation_id: Optional correlation ID for tracing.

        Returns:
            bool: True if event was published successfully, False otherwise.
        """
        # Create event envelope
        event = {
            "schema_version": "1.0",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "metadata": {
                "correlation_id": correlation_id or str(uuid4()),
                "source": settings.APP_NAME,
            },
        }

        # Use event_type as key for consistent partitioning
        key = event_type

        return await self.publish(topic, event, key)

    async def publish_batch(
        self,
        topic: str,
        messages: list[Dict[str, Any]],
    ) -> int:
        """
        Publish a batch of messages to a Kafka topic.

        Args:
            topic: Topic name to publish to.
            messages: List of message data to publish.

        Returns:
            int: Number of successfully published messages.
        """
        if self._producer is None:
            logger.error("Kafka producer is not initialized")
            return 0

        success_count = 0
        for message in messages:
            if await self.publish(topic, message):
                success_count += 1

        logger.info(
            f"Batch publish completed: {success_count}/{len(messages)} messages sent"
        )
        return success_count

    @property
    def is_connected(self) -> bool:
        """Check if the producer is connected."""
        return self._producer is not None


# Global publisher instance
_kafka_publisher: Optional[KafkaPublisher] = None


def get_kafka_publisher() -> KafkaPublisher:
    """
    Get the global Kafka publisher instance.

    Returns:
        KafkaPublisher: Global Kafka publisher instance.
    """
    global _kafka_publisher
    if _kafka_publisher is None:
        _kafka_publisher = KafkaPublisher()
    return _kafka_publisher
