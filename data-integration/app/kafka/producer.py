"""
Kafka producer for the Data Integration module.

Publishes processed events and notifications to Kafka topics.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.config import settings
from app.models.events import EventMessage

logger = structlog.get_logger(__name__)


class KafkaProducerManager:
    """
    Manages Kafka producer connections and message publishing.

    Provides async message publishing with serialization and error handling.
    """

    def __init__(self):
        """Initialize the Kafka producer manager."""
        self._producer: Optional[AIOKafkaProducer] = None
        self._connected = False
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "by_topic": {},
            "total_bytes_sent": 0,
        }

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._connected:
            logger.warning("Producer is already connected")
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=self._serialize_message,
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",  # Wait for all replicas
                compression_type="gzip",
                max_batch_size=16384,
                linger_ms=10,
                retry_backoff_ms=100,
                max_request_size=1048576,  # 1MB
            )

            await self._producer.start()
            self._connected = True

            logger.info(
                "Kafka producer started",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            )

        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e))
            self._connected = False
            raise

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if not self._connected:
            return

        if self._producer:
            try:
                # Flush pending messages
                await self._producer.flush()
                await self._producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error("Error stopping Kafka producer", error=str(e))

        self._producer = None
        self._connected = False

    def is_connected(self) -> bool:
        """Check if the producer is connected."""
        return self._connected

    def _serialize_message(self, message: Any) -> bytes:
        """
        Serialize a message to bytes.

        Args:
            message: Message to serialize

        Returns:
            Serialized bytes
        """
        if isinstance(message, EventMessage):
            data = message.model_dump()
        elif isinstance(message, dict):
            data = message
        else:
            data = {"value": message}

        # Custom JSON encoder for UUID and datetime
        def json_encoder(obj):
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(data, default=json_encoder).encode("utf-8")

    async def send(
        self,
        topic: str,
        message: Any,
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        partition: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to a Kafka topic.

        Args:
            topic: Target topic
            message: Message to send (EventMessage or dict)
            key: Optional partition key
            headers: Optional message headers
            partition: Optional specific partition

        Returns:
            Dict with send result (partition, offset)
        """
        if not self._connected:
            raise RuntimeError("Producer is not connected")

        try:
            # Convert headers to Kafka format
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode("utf-8")) for k, v in headers.items()
                ]

            # Send the message
            result = await self._producer.send_and_wait(
                topic,
                value=message,
                key=key,
                headers=kafka_headers,
                partition=partition,
            )

            # Update stats
            self._stats["messages_sent"] += 1
            self._stats["by_topic"][topic] = self._stats["by_topic"].get(topic, 0) + 1

            # Estimate bytes sent
            serialized = self._serialize_message(message)
            self._stats["total_bytes_sent"] += len(serialized)

            logger.debug(
                "Message sent",
                topic=topic,
                partition=result.partition,
                offset=result.offset,
                key=key,
            )

            return {
                "topic": topic,
                "partition": result.partition,
                "offset": result.offset,
                "timestamp": result.timestamp,
            }

        except KafkaError as e:
            self._stats["messages_failed"] += 1
            logger.error(
                "Failed to send message",
                topic=topic,
                error=str(e),
            )
            raise

    async def send_batch(
        self,
        topic: str,
        messages: List[Any],
        keys: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send multiple messages to a topic.

        Args:
            topic: Target topic
            messages: List of messages to send
            keys: Optional list of partition keys

        Returns:
            List of send results
        """
        if not self._connected:
            raise RuntimeError("Producer is not connected")

        results = []
        futures = []

        try:
            for i, message in enumerate(messages):
                key = keys[i] if keys and i < len(keys) else None

                # Send without waiting
                future = await self._producer.send(
                    topic,
                    value=message,
                    key=key,
                )
                futures.append((future, message))

            # Wait for all messages
            for future, message in futures:
                result = await future
                results.append({
                    "topic": topic,
                    "partition": result.partition,
                    "offset": result.offset,
                    "timestamp": result.timestamp,
                })

                # Update stats
                self._stats["messages_sent"] += 1
                self._stats["by_topic"][topic] = self._stats["by_topic"].get(topic, 0) + 1

            logger.info(
                "Batch sent",
                topic=topic,
                count=len(messages),
            )

            return results

        except KafkaError as e:
            self._stats["messages_failed"] += len(messages) - len(results)
            logger.error(
                "Batch send failed",
                topic=topic,
                error=str(e),
            )
            raise

    async def send_to_multiple_topics(
        self,
        messages: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send messages to multiple topics.

        Args:
            messages: Dict mapping topic names to messages

        Returns:
            Dict mapping topic names to send results
        """
        if not self._connected:
            raise RuntimeError("Producer is not connected")

        results = {}

        for topic, message in messages.items():
            try:
                result = await self.send(topic, message)
                results[topic] = {"status": "success", "result": result}
            except Exception as e:
                results[topic] = {"status": "failed", "error": str(e)}
                logger.error(
                    "Failed to send to topic",
                    topic=topic,
                    error=str(e),
                )

        return results

    async def flush(self) -> None:
        """Flush all pending messages."""
        if self._producer:
            await self._producer.flush()
            logger.debug("Producer flushed")

    async def get_partitions(self, topic: str) -> List[int]:
        """
        Get partitions for a topic.

        Args:
            topic: Topic name

        Returns:
            List of partition numbers
        """
        if not self._producer:
            return []

        try:
            partitions = await self._producer.partitions_for(topic)
            return list(partitions) if partitions else []
        except Exception as e:
            logger.error("Failed to get partitions", topic=topic, error=str(e))
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get producer statistics.

        Returns:
            Dict containing producer stats
        """
        return {
            "connected": self._connected,
            "messages_sent": self._stats["messages_sent"],
            "messages_failed": self._stats["messages_failed"],
            "success_rate": (
                self._stats["messages_sent"]
                / (self._stats["messages_sent"] + self._stats["messages_failed"])
                * 100
                if (self._stats["messages_sent"] + self._stats["messages_failed"]) > 0
                else 0
            ),
            "total_bytes_sent": self._stats["total_bytes_sent"],
            "by_topic": self._stats["by_topic"],
        }

    def reset_stats(self) -> None:
        """Reset producer statistics."""
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "by_topic": {},
            "total_bytes_sent": 0,
        }
        logger.info("Producer stats reset")
