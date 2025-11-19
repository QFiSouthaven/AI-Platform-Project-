"""
Kafka producer for sending processing results.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from aiokafka import AIOKafkaProducer

from app.config import settings

logger = structlog.get_logger(__name__)


class KafkaProducerService:
    """
    Kafka producer service for sending processing results.

    Sends results back to Kafka topics after processing is complete.
    """

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.is_connected = False

    async def start(self):
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None
            )

            await self.producer.start()
            self.is_connected = True

            logger.info(
                "Kafka producer started",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )

        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e))
            self.is_connected = False
            raise

    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.is_connected = False
            logger.info("Kafka producer stopped")

    async def send(
        self,
        topic: str,
        message: Dict[str, Any],
        correlation_id: Optional[str] = None,
        key: Optional[str] = None
    ):
        """
        Send a message to a Kafka topic.

        Args:
            topic: Target topic
            message: Message to send
            correlation_id: Request correlation ID
            key: Message key for partitioning
        """
        if not self.is_connected or not self.producer:
            logger.warning("Producer not connected, skipping message")
            return

        try:
            # Add metadata
            enriched_message = {
                "schema_version": "1.0",
                "event_type": topic.split(".")[-1],
                "timestamp": datetime.utcnow().isoformat(),
                "data": message.get("data", message),
                "metadata": {
                    "correlation_id": correlation_id,
                    "source": "core-processing",
                    **(message.get("metadata", {}))
                }
            }

            await self.producer.send_and_wait(
                topic=topic,
                value=enriched_message,
                key=key or correlation_id
            )

            logger.debug(
                "Message sent to Kafka",
                topic=topic,
                correlation_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to send message to Kafka",
                topic=topic,
                error=str(e),
                correlation_id=correlation_id
            )
            raise

    async def send_generation_result(
        self,
        result: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Send code generation result.

        Args:
            result: Generation result
            correlation_id: Request correlation ID
        """
        await self.send(
            topic=settings.KAFKA_TOPIC_GENERATION_RESULT,
            message=result,
            correlation_id=correlation_id
        )

    async def send_debug_result(
        self,
        result: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Send debugging result.

        Args:
            result: Debug result
            correlation_id: Request correlation ID
        """
        await self.send(
            topic=settings.KAFKA_TOPIC_DEBUG_RESULT,
            message=result,
            correlation_id=correlation_id
        )

    async def send_optimize_result(
        self,
        result: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Send optimization result.

        Args:
            result: Optimization result
            correlation_id: Request correlation ID
        """
        await self.send(
            topic=settings.KAFKA_TOPIC_OPTIMIZE_RESULT,
            message=result,
            correlation_id=correlation_id
        )

    async def send_evaluate_result(
        self,
        result: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Send evaluation result.

        Args:
            result: Evaluation result
            correlation_id: Request correlation ID
        """
        await self.send(
            topic=settings.KAFKA_TOPIC_EVALUATE_RESULT,
            message=result,
            correlation_id=correlation_id
        )

    async def send_error(
        self,
        topic: str,
        error: str,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send an error message.

        Args:
            topic: Target topic
            error: Error message
            correlation_id: Request correlation ID
            details: Additional error details
        """
        error_message = {
            "status": "error",
            "error": {
                "message": error,
                "details": details
            }
        }

        await self.send(
            topic=topic,
            message=error_message,
            correlation_id=correlation_id
        )

    async def send_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        """
        Send a generic event.

        Args:
            event_type: Type of event
            data: Event data
            correlation_id: Request correlation ID
        """
        topic = f"processing.{event_type}"

        await self.send(
            topic=topic,
            message={"data": data},
            correlation_id=correlation_id
        )

    def get_status(self) -> Dict[str, Any]:
        """Get producer status."""
        return {
            "connected": self.is_connected,
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS
        }
