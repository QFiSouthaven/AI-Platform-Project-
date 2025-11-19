"""
Workflow execution orchestrator.

Handles the execution of workflows, task coordination, and result aggregation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import ExecutionStatus
from app.models.task import TaskStatus
from app.services.workflow_service import WorkflowService
from app.services.task_service import TaskService
from app.services.scheduler import TaskScheduler, task_scheduler
from app.kafka.producer import KafkaProducer
from app.config import settings

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrator for managing workflow execution lifecycle."""

    def __init__(
        self,
        db: AsyncSession,
        kafka_producer: Optional[KafkaProducer] = None
    ):
        """
        Initialize the orchestrator.

        Args:
            db: Database session
            kafka_producer: Kafka producer for publishing events
        """
        self.db = db
        self.workflow_service = WorkflowService(db)
        self.task_service = TaskService(db)
        self.scheduler = task_scheduler
        self.kafka_producer = kafka_producer

    async def start_execution(
        self,
        workflow_id: int,
        execution_id: int
    ) -> bool:
        """
        Start a workflow execution.

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID

        Returns:
            True if started successfully, False otherwise
        """
        # Get workflow and execution
        workflow = await self.workflow_service.get_workflow(workflow_id)
        execution = await self.workflow_service.get_execution(execution_id)

        if not workflow or not execution:
            logger.error(
                f"Workflow or execution not found",
                extra={"workflow_id": workflow_id, "execution_id": execution_id}
            )
            return False

        # Update execution status to running
        await self.workflow_service.update_execution_status(
            execution_id,
            ExecutionStatus.RUNNING
        )

        # Publish event
        if self.kafka_producer:
            await self.kafka_producer.publish_workflow_event(
                "workflow.started",
                {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "correlation_id": execution.correlation_id,
                }
            )

        # Create task executions for all tasks
        tasks = workflow.tasks
        task_execution_map = {}

        for task in tasks:
            task_execution = await self.task_service.create_task_execution(
                task.id,
                execution_id
            )
            task_execution_map[task.id] = task_execution

        # Resolve task execution order
        ordered_tasks = await self.scheduler.resolve_task_order(tasks)

        # Execute tasks
        try:
            await self._execute_tasks(
                workflow_id,
                execution_id,
                ordered_tasks,
                task_execution_map
            )
        except Exception as e:
            logger.error(
                f"Workflow execution failed: {e}",
                extra={
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "error": str(e)
                }
            )
            await self.workflow_service.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED,
                error_message=str(e)
            )
            return False

        return True

    async def _execute_tasks(
        self,
        workflow_id: int,
        execution_id: int,
        tasks: list,
        task_execution_map: dict
    ) -> None:
        """
        Execute tasks in dependency order.

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID
            tasks: Ordered list of tasks
            task_execution_map: Map of task IDs to task executions
        """
        completed_task_ids = set()
        failed = False

        while len(completed_task_ids) < len(tasks) and not failed:
            # Get executable tasks
            executable = await self.scheduler.get_executable_tasks(
                tasks,
                completed_task_ids
            )

            if not executable:
                # No more tasks can be executed
                if len(completed_task_ids) < len(tasks):
                    # There are remaining tasks but none are executable
                    # This could indicate a dependency cycle or all remaining tasks failed
                    failed = True
                    break
                break

            # Execute tasks in parallel
            results = await asyncio.gather(
                *[
                    self._execute_single_task(
                        task,
                        task_execution_map[task.id],
                        execution_id
                    )
                    for task in executable
                ],
                return_exceptions=True
            )

            # Process results
            for task, result in zip(executable, results):
                task_execution = task_execution_map[task.id]

                if isinstance(result, Exception):
                    # Task failed
                    await self.task_service.update_task_execution_status(
                        task_execution.id,
                        TaskStatus.FAILED,
                        error_message=str(result)
                    )

                    # Check if should retry
                    if await self.scheduler.should_retry(task_execution, task):
                        delay = self.scheduler.calculate_retry_delay(
                            task,
                            task_execution.retry_count
                        )
                        await self.task_service.increment_retry_count(task_execution.id)
                        await asyncio.sleep(delay)
                        # Re-execute will happen in next iteration
                    else:
                        failed = True
                        break
                else:
                    # Task completed successfully
                    completed_task_ids.add(task.id)

        # Update workflow execution status
        execution = await self.workflow_service.get_execution(execution_id)

        if failed:
            status = ExecutionStatus.FAILED
            error_message = "One or more tasks failed"
        else:
            status = ExecutionStatus.COMPLETED
            error_message = None

        # Aggregate output data from all tasks
        output_data = {}
        for task in tasks:
            task_exec = task_execution_map[task.id]
            refreshed = await self.task_service.get_task_execution(task_exec.id)
            if refreshed and refreshed.output_data:
                output_data[task.name] = refreshed.output_data

        await self.workflow_service.update_execution_status(
            execution_id,
            status,
            error_message=error_message,
            output_data=output_data
        )

        # Publish completion event
        if self.kafka_producer:
            await self.kafka_producer.publish_workflow_event(
                "workflow.completed" if not failed else "workflow.failed",
                {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "status": status.value,
                    "correlation_id": execution.correlation_id,
                }
            )

    async def _execute_single_task(
        self,
        task,
        task_execution,
        execution_id: int
    ) -> dict:
        """
        Execute a single task.

        Args:
            task: Task to execute
            task_execution: Task execution record
            execution_id: Workflow execution ID

        Returns:
            Task output data
        """
        # Update status to running
        await self.task_service.update_task_execution_status(
            task_execution.id,
            TaskStatus.RUNNING,
            worker_id=f"worker-{execution_id}"
        )

        # Publish task started event
        if self.kafka_producer:
            await self.kafka_producer.publish_task_event(
                "task.started",
                {
                    "task_id": task.id,
                    "task_execution_id": task_execution.id,
                    "workflow_execution_id": execution_id,
                    "task_type": task.task_type.value,
                }
            )

        try:
            # Execute based on task type
            output = await self._dispatch_task(task, task_execution)

            # Update status to completed
            await self.task_service.update_task_execution_status(
                task_execution.id,
                TaskStatus.COMPLETED,
                output_data=output
            )

            # Publish task completed event
            if self.kafka_producer:
                await self.kafka_producer.publish_task_event(
                    "task.completed",
                    {
                        "task_id": task.id,
                        "task_execution_id": task_execution.id,
                        "workflow_execution_id": execution_id,
                    }
                )

            return output

        except asyncio.TimeoutError:
            # Handle timeout
            await self.task_service.update_task_execution_status(
                task_execution.id,
                TaskStatus.TIMEOUT,
                error_message="Task execution timed out"
            )
            raise

        except Exception as e:
            # Publish task failed event
            if self.kafka_producer:
                await self.kafka_producer.publish_task_event(
                    "task.failed",
                    {
                        "task_id": task.id,
                        "task_execution_id": task_execution.id,
                        "workflow_execution_id": execution_id,
                        "error": str(e),
                    }
                )
            raise

    async def _dispatch_task(self, task, task_execution) -> dict:
        """
        Dispatch task execution based on task type.

        Args:
            task: Task definition
            task_execution: Task execution record

        Returns:
            Task output data
        """
        task_type = task.task_type.value
        config = task.config

        # Apply timeout
        timeout = task.timeout_seconds

        if task_type == "code_generation":
            return await asyncio.wait_for(
                self._execute_code_generation(config),
                timeout=timeout
            )
        elif task_type == "data_processing":
            return await asyncio.wait_for(
                self._execute_data_processing(config),
                timeout=timeout
            )
        elif task_type == "model_inference":
            return await asyncio.wait_for(
                self._execute_model_inference(config),
                timeout=timeout
            )
        elif task_type == "api_call":
            return await asyncio.wait_for(
                self._execute_api_call(config),
                timeout=timeout
            )
        elif task_type == "notification":
            return await asyncio.wait_for(
                self._execute_notification(config),
                timeout=timeout
            )
        elif task_type == "conditional":
            return await asyncio.wait_for(
                self._execute_conditional(config),
                timeout=timeout
            )
        elif task_type == "aggregation":
            return await asyncio.wait_for(
                self._execute_aggregation(config),
                timeout=timeout
            )
        elif task_type == "transform":
            return await asyncio.wait_for(
                self._execute_transform(config),
                timeout=timeout
            )
        elif task_type == "validation":
            return await asyncio.wait_for(
                self._execute_validation(config),
                timeout=timeout
            )
        else:
            return await asyncio.wait_for(
                self._execute_custom(config),
                timeout=timeout
            )

    async def _execute_code_generation(self, config: dict) -> dict:
        """Execute code generation task."""
        # TODO: Integrate with Core Processing module
        logger.info(f"Executing code generation with config: {config}")
        await asyncio.sleep(1)  # Simulate work
        return {"status": "completed", "result": "code_generated"}

    async def _execute_data_processing(self, config: dict) -> dict:
        """Execute data processing task."""
        # TODO: Integrate with Data Integration module
        logger.info(f"Executing data processing with config: {config}")
        await asyncio.sleep(1)
        return {"status": "completed", "result": "data_processed"}

    async def _execute_model_inference(self, config: dict) -> dict:
        """Execute model inference task."""
        # TODO: Integrate with Model Management module
        logger.info(f"Executing model inference with config: {config}")
        await asyncio.sleep(1)
        return {"status": "completed", "result": "inference_complete"}

    async def _execute_api_call(self, config: dict) -> dict:
        """Execute API call task."""
        import httpx

        url = config.get("url")
        method = config.get("method", "GET")
        headers = config.get("headers", {})
        body = config.get("body")

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                json=body
            )
            return {
                "status_code": response.status_code,
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }

    async def _execute_notification(self, config: dict) -> dict:
        """Execute notification task."""
        logger.info(f"Sending notification: {config}")
        await asyncio.sleep(0.5)
        return {"status": "sent", "channel": config.get("channel", "email")}

    async def _execute_conditional(self, config: dict) -> dict:
        """Execute conditional task."""
        condition = config.get("condition", True)
        return {"condition_met": bool(condition)}

    async def _execute_aggregation(self, config: dict) -> dict:
        """Execute aggregation task."""
        logger.info(f"Executing aggregation with config: {config}")
        await asyncio.sleep(0.5)
        return {"status": "aggregated"}

    async def _execute_transform(self, config: dict) -> dict:
        """Execute transform task."""
        logger.info(f"Executing transform with config: {config}")
        await asyncio.sleep(0.5)
        return {"status": "transformed"}

    async def _execute_validation(self, config: dict) -> dict:
        """Execute validation task."""
        logger.info(f"Executing validation with config: {config}")
        await asyncio.sleep(0.5)
        return {"status": "validated", "valid": True}

    async def _execute_custom(self, config: dict) -> dict:
        """Execute custom task."""
        logger.info(f"Executing custom task with config: {config}")
        await asyncio.sleep(1)
        return {"status": "completed"}

    async def cancel_execution(self, execution_id: int) -> bool:
        """
        Cancel a running execution.

        Args:
            execution_id: Execution ID

        Returns:
            True if cancelled, False otherwise
        """
        execution = await self.workflow_service.get_execution(execution_id)
        if not execution:
            return False

        if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
            return False

        # Cancel scheduled job
        self.scheduler.cancel_workflow(execution.workflow_id, execution_id)

        # Update status
        await self.workflow_service.cancel_execution(execution_id)

        # Cancel running task executions
        for task_exec in execution.task_executions:
            if task_exec.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.QUEUED]:
                await self.task_service.update_task_execution_status(
                    task_exec.id,
                    TaskStatus.CANCELLED,
                    error_message="Workflow execution cancelled"
                )

        # Publish event
        if self.kafka_producer:
            await self.kafka_producer.publish_workflow_event(
                "workflow.cancelled",
                {
                    "workflow_id": execution.workflow_id,
                    "execution_id": execution_id,
                    "correlation_id": execution.correlation_id,
                }
            )

        logger.info(f"Cancelled execution: {execution_id}")
        return True

    async def retry_execution(self, execution_id: int) -> Optional[int]:
        """
        Retry a failed execution.

        Args:
            execution_id: Original execution ID

        Returns:
            New execution ID if created, None otherwise
        """
        execution = await self.workflow_service.get_execution(execution_id)
        if not execution:
            return None

        if execution.status != ExecutionStatus.FAILED:
            return None

        # Create new execution with same input
        from app.models.schemas import WorkflowExecutionCreate

        new_execution = await self.workflow_service.create_execution(
            execution.workflow_id,
            WorkflowExecutionCreate(
                input_data=execution.input_data,
                triggered_by=f"retry:{execution.triggered_by}"
            )
        )

        if new_execution:
            logger.info(
                f"Created retry execution {new_execution.id} for failed execution {execution_id}"
            )
            return new_execution.id

        return None
