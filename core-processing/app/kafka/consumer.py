"""
Kafka consumer for processing tasks from the message queue.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from aiokafka import AIOKafkaConsumer

# Windows-specific: Ensure proper event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.config import settings
from app.models.llm_models import (
    DebugRequest,
    GenerationRequest,
    OptimizationRequest,
    ProgrammingLanguage,
)
from app.models.evaluation import EvaluationRequest
from app.services.code_generator import CodeGeneratorService
from app.services.debugger import DebuggerService
from app.services.evaluator import EvaluatorService
from app.services.llm_service import LLMService
from app.services.optimizer import OptimizerService

logger = structlog.get_logger(__name__)


class KafkaConsumerService:
    """
    Kafka consumer service for processing code tasks.

    Listens to multiple topics for different task types and
    processes them using the appropriate service.
    """

    def __init__(
        self,
        llm_service: LLMService,
        producer: Optional[Any] = None
    ):
        self.llm_service = llm_service
        self.producer = producer
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.is_running = False

        # Initialize services
        self.code_generator = CodeGeneratorService(llm_service)
        self.debugger = DebuggerService(llm_service)
        self.optimizer = OptimizerService(llm_service)
        self.evaluator = EvaluatorService(llm_service)

        # Topic handlers
        self.topic_handlers = {
            settings.KAFKA_TOPIC_GENERATION_REQUEST: self._handle_generation,
            settings.KAFKA_TOPIC_DEBUG_REQUEST: self._handle_debug,
            settings.KAFKA_TOPIC_OPTIMIZE_REQUEST: self._handle_optimize,
            settings.KAFKA_TOPIC_EVALUATE_REQUEST: self._handle_evaluate,
        }

    async def start(self):
        """Start the Kafka consumer."""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topic_handlers.keys(),
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=settings.KAFKA_ENABLE_AUTO_COMMIT,
                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
            )

            await self.consumer.start()
            self.is_running = True

            logger.info(
                "Kafka consumer started",
                topics=list(self.topic_handlers.keys()),
                group_id=settings.KAFKA_CONSUMER_GROUP
            )

            # Start consuming messages
            await self._consume_messages()

        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise

    async def stop(self):
        """Stop the Kafka consumer."""
        self.is_running = False

        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def _consume_messages(self):
        """Consume and process messages from Kafka."""
        try:
            async for message in self.consumer:
                if not self.is_running:
                    break

                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(
                        "Failed to process message",
                        topic=message.topic,
                        error=str(e)
                    )

        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        except Exception as e:
            logger.error("Consumer error", error=str(e))

    async def _process_message(self, message):
        """
        Process a single Kafka message.

        Args:
            message: Kafka message
        """
        topic = message.topic
        data = message.value
        correlation_id = data.get("metadata", {}).get("correlation_id")

        logger.info(
            "Processing message",
            topic=topic,
            correlation_id=correlation_id
        )

        handler = self.topic_handlers.get(topic)
        if handler:
            result = await handler(data)

            # Send result to producer if available
            if self.producer and result:
                result_topic = self._get_result_topic(topic)
                await self.producer.send(result_topic, result, correlation_id)

        else:
            logger.warning(f"No handler for topic: {topic}")

    def _get_result_topic(self, request_topic: str) -> str:
        """Get the result topic for a request topic."""
        topic_mapping = {
            settings.KAFKA_TOPIC_GENERATION_REQUEST: settings.KAFKA_TOPIC_GENERATION_RESULT,
            settings.KAFKA_TOPIC_DEBUG_REQUEST: settings.KAFKA_TOPIC_DEBUG_RESULT,
            settings.KAFKA_TOPIC_OPTIMIZE_REQUEST: settings.KAFKA_TOPIC_OPTIMIZE_RESULT,
            settings.KAFKA_TOPIC_EVALUATE_REQUEST: settings.KAFKA_TOPIC_EVALUATE_RESULT,
        }
        return topic_mapping.get(request_topic, f"{request_topic}.result")

    async def _handle_generation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code generation request."""
        try:
            request_data = data.get("data", {})

            request = GenerationRequest(
                prompt=request_data.get("prompt", ""),
                language=ProgrammingLanguage(request_data.get("language", "python")),
                context=request_data.get("context"),
                requirements=request_data.get("requirements"),
                correlation_id=data.get("metadata", {}).get("correlation_id")
            )

            response = await self.code_generator.generate(request)

            return {
                "status": "success",
                "data": {
                    "code": response.code,
                    "language": response.language,
                    "tokens_used": response.tokens_used,
                    "generation_time_ms": response.generation_time_ms
                },
                "metadata": {
                    "correlation_id": response.correlation_id,
                    "model_name": response.model_name
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("Generation handler failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metadata": data.get("metadata", {}),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_debug(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle debugging request."""
        try:
            request_data = data.get("data", {})

            request = DebugRequest(
                code=request_data.get("code", ""),
                language=ProgrammingLanguage(request_data.get("language", "python")),
                error_message=request_data.get("error_message"),
                stack_trace=request_data.get("stack_trace"),
                correlation_id=data.get("metadata", {}).get("correlation_id")
            )

            response = await self.debugger.debug(request)

            return {
                "status": "success",
                "data": {
                    "fixed_code": response.fixed_code,
                    "bugs_found": [bug.model_dump() for bug in response.bugs_found],
                    "analysis": response.analysis,
                    "tokens_used": response.tokens_used
                },
                "metadata": {
                    "correlation_id": response.correlation_id,
                    "model_name": response.model_name
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("Debug handler failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metadata": data.get("metadata", {}),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_optimize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle optimization request."""
        try:
            request_data = data.get("data", {})

            request = OptimizationRequest(
                code=request_data.get("code", ""),
                language=ProgrammingLanguage(request_data.get("language", "python")),
                optimization_goals=request_data.get("optimization_goals"),
                preserve_behavior=request_data.get("preserve_behavior", True),
                correlation_id=data.get("metadata", {}).get("correlation_id")
            )

            response = await self.optimizer.optimize(request)

            return {
                "status": "success",
                "data": {
                    "optimized_code": response.optimized_code,
                    "optimizations": [opt.model_dump() for opt in response.optimizations],
                    "summary": response.summary,
                    "tokens_used": response.tokens_used
                },
                "metadata": {
                    "correlation_id": response.correlation_id,
                    "model_name": response.model_name
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("Optimize handler failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metadata": data.get("metadata", {}),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _handle_evaluate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle evaluation request."""
        try:
            request_data = data.get("data", {})

            request = EvaluationRequest(
                code=request_data.get("code", ""),
                language=ProgrammingLanguage(request_data.get("language", "python")),
                evaluation_criteria=request_data.get("evaluation_criteria"),
                include_suggestions=request_data.get("include_suggestions", True),
                correlation_id=data.get("metadata", {}).get("correlation_id")
            )

            response = await self.evaluator.evaluate(request)

            return {
                "status": "success",
                "data": {
                    "quality_level": response.quality_level,
                    "scores": response.scores.model_dump(),
                    "metrics": response.metrics.model_dump(),
                    "issues": [issue.model_dump() for issue in response.issues],
                    "suggestions": [sugg.model_dump() for sugg in response.suggestions],
                    "summary": response.summary
                },
                "metadata": {
                    "correlation_id": response.correlation_id
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("Evaluate handler failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "metadata": data.get("metadata", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
