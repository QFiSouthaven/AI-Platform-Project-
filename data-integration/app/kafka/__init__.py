"""
Kafka integration for the Data Integration module.
"""

from app.kafka.consumer import KafkaConsumerManager
from app.kafka.producer import KafkaProducerManager

__all__ = [
    "KafkaConsumerManager",
    "KafkaProducerManager",
]
