"""
Kafka consumer for the Data Integration module.

Consumes events from multiple Kafka topics and processes them.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.config import settings
from app.models.events import EventMessage, EventMetadata

logger = structlog.get_logger(__name__)


class KafkaConsumerManager:
    """
    Manages Kafka consumer connections and message processing.

    Subscribes to multiple topics and routes messages to the event processor.
    """

    def __init__(self, topics: List[str], event_processor):
        """
        Initialize the Kafka consumer manager.

        Args:
            topics: List of topics to subscribe to
            event_processor: EventProcessor instance for handling messages
        """
        self.topics = topics
        self.event_processor = event_processor
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "by_topic": {},
        }

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._running:
            logger.warning("Consumer is already running")
            return

        try:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
                auto_commit_interval_ms=settings.KAFKA_AUTO_COMMIT_INTERVAL_MS,
                session_timeout_ms=settings.KAFKA_SESSION_TIMEOUT_MS,
                max_poll_records=settings.KAFKA_MAX_POLL_RECORDS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
            )

            await self._consumer.start()
            self._running = True

            logger.info(
                "Kafka consumer started",
                topics=self.topics,
                group_id=settings.KAFKA_GROUP_ID,
            )

            # Start consuming messages
            await self._consume_messages()

        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            self._running = False
            raise

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if not self._running:
            return

        self._running = False

        if self._consumer:
            try:
                await self._consumer.stop()
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.error("Error stopping Kafka consumer", error=str(e))

        self._consumer = None

    def is_running(self) -> bool:
        """Check if the consumer is running."""
        return self._running

    async def _consume_messages(self) -> None:
        """Main message consumption loop."""
        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(
                        "Error processing message",
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        error=str(e),
                    )
                    self._stats["messages_failed"] += 1

        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
        except Exception as e:
            logger.error("Consumer loop error", error=str(e))
            self._running = False

    async def _process_message(self, message) -> None:
        """
        Process a single Kafka message.

        Args:
            message: Kafka message from consumer
        """
        self._stats["messages_received"] += 1
        topic = message.topic
        self._stats["by_topic"][topic] = self._stats["by_topic"].get(topic, 0) + 1

        logger.debug(
            "Received message",
            topic=topic,
            partition=message.partition,
            offset=message.offset,
            key=message.key,
        )

        try:
            # Parse message value
            data = message.value
            if not isinstance(data, dict):
                logger.warning("Invalid message format", topic=topic)
                return

            # Create EventMessage from Kafka message
            event = self._parse_event_message(data, topic)

            # Process the event
            processed = await self.event_processor.process_event(event)

            if processed.status == "success":
                self._stats["messages_processed"] += 1
            else:
                self._stats["messages_failed"] += 1

            logger.debug(
                "Message processed",
                event_id=str(event.event_id),
                status=processed.status,
                duration_ms=processed.processing_duration_ms,
            )

        except Exception as e:
            logger.error(
                "Failed to process message",
                topic=topic,
                error=str(e),
            )
            self._stats["messages_failed"] += 1
            raise

    def _parse_event_message(self, data: Dict[str, Any], topic: str) -> EventMessage:
        """
        Parse raw message data into EventMessage.

        Args:
            data: Raw message data
            topic: Source topic

        Returns:
            EventMessage instance
        """
        # Handle different message formats
        if "event_type" in data and "data" in data:
            # Standard event format
            metadata_data = data.get("metadata", {})
            metadata = EventMetadata(
                correlation_id=metadata_data.get("correlation_id"),
                source=metadata_data.get("source", topic),
                user_id=metadata_data.get("user_id"),
                trace_id=metadata_data.get("trace_id"),
                span_id=metadata_data.get("span_id"),
                retry_count=metadata_data.get("retry_count", 0),
                priority=metadata_data.get("priority", 0),
            )

            return EventMessage(
                schema_version=data.get("schema_version", "1.0"),
                event_id=data.get("event_id"),
                event_type=data.get("event_type"),
                timestamp=data.get("timestamp"),
                data=data.get("data", {}),
                metadata=metadata,
            )
        else:
            # Legacy format - wrap the entire payload
            return EventMessage(
                event_type=topic,
                data=data,
                metadata=EventMetadata(
                    source=topic,
                ),
            )

    async def commit(self) -> None:
        """Manually commit offsets."""
        if self._consumer:
            await self._consumer.commit()
            logger.debug("Offsets committed")

    async def seek_to_beginning(self, topic: str = None) -> None:
        """
        Seek to the beginning of topics.

        Args:
            topic: Optional specific topic to seek
        """
        if self._consumer:
            partitions = self._consumer.assignment()
            if topic:
                partitions = [p for p in partitions if p.topic == topic]
            await self._consumer.seek_to_beginning(*partitions)
            logger.info("Seeked to beginning", topic=topic)

    async def seek_to_end(self, topic: str = None) -> None:
        """
        Seek to the end of topics.

        Args:
            topic: Optional specific topic to seek
        """
        if self._consumer:
            partitions = self._consumer.assignment()
            if topic:
                partitions = [p for p in partitions if p.topic == topic]
            await self._consumer.seek_to_end(*partitions)
            logger.info("Seeked to end", topic=topic)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get consumer statistics.

        Returns:
            Dict containing consumer stats
        """
        return {
            "running": self._running,
            "topics": self.topics,
            "group_id": settings.KAFKA_GROUP_ID,
            "messages_received": self._stats["messages_received"],
            "messages_processed": self._stats["messages_processed"],
            "messages_failed": self._stats["messages_failed"],
            "success_rate": (
                self._stats["messages_processed"]
                / self._stats["messages_received"]
                * 100
                if self._stats["messages_received"] > 0
                else 0
            ),
            "by_topic": self._stats["by_topic"],
        }

    async def get_lag(self) -> Dict[str, Any]:
        """
        Get consumer lag information.

        Returns:
            Dict with lag per topic/partition
        """
        if not self._consumer:
            return {}

        lag_info = {}
        try:
            partitions = self._consumer.assignment()
            for partition in partitions:
                # Get current position
                position = await self._consumer.position(partition)

                # Get end offset
                end_offsets = await self._consumer.end_offsets([partition])
                end_offset = end_offsets.get(partition, 0)

                lag = end_offset - position if end_offset > position else 0

                topic_key = partition.topic
                if topic_key not in lag_info:
                    lag_info[topic_key] = {}
                lag_info[topic_key][partition.partition] = {
                    "position": position,
                    "end_offset": end_offset,
                    "lag": lag,
                }

        except Exception as e:
            logger.error("Failed to get consumer lag", error=str(e))

        return lag_info

    def reset_stats(self) -> None:
        """Reset consumer statistics."""
        self._stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "by_topic": {},
        }
        logger.info("Consumer stats reset")
