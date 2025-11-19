"""
Kafka integration for Core Processing module.
"""

from app.kafka.consumer import KafkaConsumerService
from app.kafka.producer import KafkaProducerService

__all__ = [
    "KafkaConsumerService",
    "KafkaProducerService",
]
