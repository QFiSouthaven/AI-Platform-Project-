"""
Task service for task management operations.
"""

import logging
from typing import Optional
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskExecution, TaskStatus
from app.models.workflow import WorkflowExecution
from app.models.schemas import TaskCreate, TaskUpdate, PaginationParams

logger = logging.getLogger(__name__)


class TaskService:
    """Service for managing tasks and their executions."""

    def __init__(self, db: AsyncSession):
        """
        Initialize task service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_task(
        self,
        workflow_id: int,
        task_data: TaskCreate
    ) -> Task:
        """
        Create a new task for a workflow.

        Args:
            workflow_id: Workflow ID
            task_data: Task creation data

        Returns:
            Created task
        """
        task = Task(
            workflow_id=workflow_id,
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            config=task_data.config,
            depends_on=task_data.depends_on,
            retry_policy=task_data.retry_policy.model_dump(),
            timeout_seconds=task_data.timeout_seconds,
            priority=task_data.priority,
            metadata=task_data.metadata,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        logger.info(
            f"Created task: {task.id}",
            extra={
                "task_id": task.id,
                "workflow_id": workflow_id,
                "task_name": task.name
            }
        )

        return task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        query = select(Task).where(Task.id == task_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        workflow_id: int,
        pagination: PaginationParams
    ) -> tuple[list[Task], int]:
        """
        List tasks for a workflow with pagination.

        Args:
            workflow_id: Workflow ID
            pagination: Pagination parameters

        Returns:
            Tuple of tasks list and total count
        """
        # Count query
        count_query = (
            select(func.count(Task.id))
            .where(Task.workflow_id == workflow_id)
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # List query with pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = (
            select(Task)
            .where(Task.workflow_id == workflow_id)
            .order_by(Task.priority.desc(), Task.id)
            .offset(offset)
            .limit(pagination.page_size)
        )
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        return list(tasks), total

    async def update_task(
        self,
        task_id: int,
        task_data: TaskUpdate
    ) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task ID
            task_data: Update data

        Returns:
            Updated task if found, None otherwise
        """
        task = await self.get_task(task_id)
        if not task:
            return None

        # Update fields
        update_data = task_data.model_dump(exclude_unset=True)

        # Handle retry_policy separately
        if "retry_policy" in update_data and update_data["retry_policy"]:
            update_data["retry_policy"] = update_data["retry_policy"].model_dump()

        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)

        logger.info(
            f"Updated task: {task_id}",
            extra={"task_id": task_id, "updates": list(update_data.keys())}
        )

        return task

    async def delete_task(self, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        task = await self.get_task(task_id)
        if not task:
            return False

        await self.db.delete(task)
        await self.db.commit()

        logger.info(f"Deleted task: {task_id}")
        return True

    async def create_task_execution(
        self,
        task_id: int,
        workflow_execution_id: int
    ) -> TaskExecution:
        """
        Create a task execution record.

        Args:
            task_id: Task ID
            workflow_execution_id: Workflow execution ID

        Returns:
            Created task execution
        """
        task_execution = TaskExecution(
            task_id=task_id,
            workflow_execution_id=workflow_execution_id,
            status=TaskStatus.PENDING,
        )
        self.db.add(task_execution)
        await self.db.commit()
        await self.db.refresh(task_execution)

        logger.info(
            f"Created task execution: {task_execution.id}",
            extra={
                "task_execution_id": task_execution.id,
                "task_id": task_id,
                "workflow_execution_id": workflow_execution_id
            }
        )

        return task_execution

    async def get_task_execution(
        self,
        task_execution_id: int
    ) -> Optional[TaskExecution]:
        """
        Get a task execution by ID.

        Args:
            task_execution_id: Task execution ID

        Returns:
            Task execution if found, None otherwise
        """
        query = select(TaskExecution).where(TaskExecution.id == task_execution_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_task_executions(
        self,
        workflow_execution_id: int,
        pagination: PaginationParams,
        status: Optional[TaskStatus] = None
    ) -> tuple[list[TaskExecution], int]:
        """
        List task executions for a workflow execution.

        Args:
            workflow_execution_id: Workflow execution ID
            pagination: Pagination parameters
            status: Filter by status

        Returns:
            Tuple of task executions list and total count
        """
        # Build query
        query = select(TaskExecution).where(
            TaskExecution.workflow_execution_id == workflow_execution_id
        )
        count_query = select(func.count(TaskExecution.id)).where(
            TaskExecution.workflow_execution_id == workflow_execution_id
        )

        if status:
            query = query.where(TaskExecution.status == status)
            count_query = count_query.where(TaskExecution.status == status)

        # Get count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = (
            query
            .order_by(TaskExecution.started_at.desc().nullslast())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(query)
        executions = result.scalars().all()

        return list(executions), total

    async def update_task_execution_status(
        self,
        task_execution_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None,
        output_data: Optional[dict] = None,
        worker_id: Optional[str] = None,
        logs: Optional[list] = None
    ) -> Optional[TaskExecution]:
        """
        Update task execution status.

        Args:
            task_execution_id: Task execution ID
            status: New status
            error_message: Error message if failed
            output_data: Output data if completed
            worker_id: Worker that processed the task
            logs: Execution logs

        Returns:
            Updated task execution if found, None otherwise
        """
        task_execution = await self.get_task_execution(task_execution_id)
        if not task_execution:
            return None

        task_execution.status = status

        if status == TaskStatus.RUNNING and not task_execution.started_at:
            task_execution.started_at = datetime.utcnow()

        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED, TaskStatus.CANCELLED]:
            task_execution.completed_at = datetime.utcnow()
            if task_execution.started_at:
                duration = (task_execution.completed_at - task_execution.started_at).total_seconds()
                task_execution.metrics["duration_seconds"] = duration

        if error_message:
            task_execution.error_message = error_message

        if output_data:
            task_execution.output_data = output_data

        if worker_id:
            task_execution.worker_id = worker_id

        if logs:
            task_execution.logs.extend(logs)

        await self.db.commit()
        await self.db.refresh(task_execution)

        logger.info(
            f"Updated task execution {task_execution_id} status to {status}",
            extra={"task_execution_id": task_execution_id, "status": status}
        )

        return task_execution

    async def increment_retry_count(
        self,
        task_execution_id: int
    ) -> Optional[TaskExecution]:
        """
        Increment retry count for a task execution.

        Args:
            task_execution_id: Task execution ID

        Returns:
            Updated task execution if found, None otherwise
        """
        task_execution = await self.get_task_execution(task_execution_id)
        if not task_execution:
            return None

        task_execution.retry_count += 1
        task_execution.status = TaskStatus.QUEUED

        await self.db.commit()
        await self.db.refresh(task_execution)

        logger.info(
            f"Incremented retry count for task execution {task_execution_id}",
            extra={
                "task_execution_id": task_execution_id,
                "retry_count": task_execution.retry_count
            }
        )

        return task_execution

    async def get_pending_task_executions(
        self,
        workflow_execution_id: int
    ) -> list[TaskExecution]:
        """
        Get pending task executions for a workflow execution.

        Args:
            workflow_execution_id: Workflow execution ID

        Returns:
            List of pending task executions
        """
        query = (
            select(TaskExecution)
            .where(
                and_(
                    TaskExecution.workflow_execution_id == workflow_execution_id,
                    TaskExecution.status == TaskStatus.PENDING
                )
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task_statistics(
        self,
        workflow_id: Optional[int] = None
    ) -> dict:
        """
        Get task statistics.

        Args:
            workflow_id: Filter by workflow ID

        Returns:
            Statistics dictionary
        """
        # Tasks by type
        type_query = select(
            Task.task_type,
            func.count(Task.id)
        ).group_by(Task.task_type)

        if workflow_id:
            type_query = type_query.where(Task.workflow_id == workflow_id)

        type_result = await self.db.execute(type_query)
        tasks_by_type = {str(k): v for k, v in type_result.all()}

        # Task executions by status
        status_query = select(
            TaskExecution.status,
            func.count(TaskExecution.id)
        ).group_by(TaskExecution.status)

        status_result = await self.db.execute(status_query)
        tasks_by_status = {str(k): v for k, v in status_result.all()}

        # Average retry count
        retry_query = select(func.avg(TaskExecution.retry_count))
        retry_result = await self.db.execute(retry_query)
        avg_retry = retry_result.scalar() or 0

        # Average duration
        duration_query = select(
            func.avg(
                func.extract(
                    'epoch',
                    TaskExecution.completed_at - TaskExecution.started_at
                )
            )
        ).where(TaskExecution.completed_at.isnot(None))

        duration_result = await self.db.execute(duration_query)
        avg_duration = duration_result.scalar() or 0

        total_tasks = sum(tasks_by_type.values())

        return {
            "total_tasks": total_tasks,
            "tasks_by_type": tasks_by_type,
            "tasks_by_status": tasks_by_status,
            "average_retry_count": round(avg_retry, 2),
            "average_duration_seconds": round(avg_duration, 2),
        }
