"""
Workflow service for CRUD operations and business logic.
"""

import logging
from typing import Optional
from datetime import datetime
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workflow import Workflow, WorkflowExecution, WorkflowStatus, ExecutionStatus
from app.models.task import Task
from app.models.schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecutionCreate,
    PaginationParams,
)
from app.config import settings

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflows and their executions."""

    def __init__(self, db: AsyncSession):
        """
        Initialize workflow service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_workflow(
        self,
        workflow_data: WorkflowCreate,
        created_by: str
    ) -> Workflow:
        """
        Create a new workflow with tasks.

        Args:
            workflow_data: Workflow creation data
            created_by: User creating the workflow

        Returns:
            Created workflow
        """
        # Create workflow
        workflow = Workflow(
            name=workflow_data.name,
            description=workflow_data.description,
            version=workflow_data.version,
            definition=workflow_data.definition,
            is_template=workflow_data.is_template,
            timeout_seconds=workflow_data.timeout_seconds,
            tags=workflow_data.tags,
            metadata=workflow_data.metadata,
            created_by=created_by,
            status=WorkflowStatus.DRAFT,
        )
        self.db.add(workflow)
        await self.db.flush()

        # Create tasks
        for task_data in workflow_data.tasks:
            task = Task(
                workflow_id=workflow.id,
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
        await self.db.refresh(workflow)

        logger.info(
            f"Created workflow: {workflow.id}",
            extra={
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "created_by": created_by
            }
        )

        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        query = (
            select(Workflow)
            .options(selectinload(Workflow.tasks))
            .where(Workflow.id == workflow_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        pagination: PaginationParams,
        status: Optional[WorkflowStatus] = None,
        created_by: Optional[str] = None,
        is_template: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Workflow], int]:
        """
        List workflows with filtering and pagination.

        Args:
            pagination: Pagination parameters
            status: Filter by status
            created_by: Filter by creator
            is_template: Filter by template flag
            search: Search in name and description

        Returns:
            Tuple of workflows list and total count
        """
        # Build base query
        query = select(Workflow).options(selectinload(Workflow.tasks))
        count_query = select(func.count(Workflow.id))

        # Apply filters
        filters = []
        if status:
            filters.append(Workflow.status == status)
        if created_by:
            filters.append(Workflow.created_by == created_by)
        if is_template is not None:
            filters.append(Workflow.is_template == is_template)
        if search:
            search_filter = f"%{search}%"
            filters.append(
                (Workflow.name.ilike(search_filter)) |
                (Workflow.description.ilike(search_filter))
            )

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = (
            query
            .order_by(Workflow.updated_at.desc())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(query)
        workflows = result.scalars().all()

        return list(workflows), total

    async def update_workflow(
        self,
        workflow_id: int,
        workflow_data: WorkflowUpdate
    ) -> Optional[Workflow]:
        """
        Update a workflow.

        Args:
            workflow_id: Workflow ID
            workflow_data: Update data

        Returns:
            Updated workflow if found, None otherwise
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        # Update fields
        update_data = workflow_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)

        await self.db.commit()
        await self.db.refresh(workflow)

        logger.info(
            f"Updated workflow: {workflow_id}",
            extra={"workflow_id": workflow_id, "updates": list(update_data.keys())}
        )

        return workflow

    async def delete_workflow(self, workflow_id: int) -> bool:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if deleted, False if not found
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return False

        await self.db.delete(workflow)
        await self.db.commit()

        logger.info(f"Deleted workflow: {workflow_id}")
        return True

    async def activate_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """
        Activate a workflow (change status from draft to active).

        Args:
            workflow_id: Workflow ID

        Returns:
            Updated workflow if found, None otherwise
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        if workflow.status != WorkflowStatus.DRAFT:
            raise ValueError(f"Cannot activate workflow with status: {workflow.status}")

        workflow.status = WorkflowStatus.ACTIVE
        await self.db.commit()
        await self.db.refresh(workflow)

        logger.info(f"Activated workflow: {workflow_id}")
        return workflow

    async def clone_workflow(
        self,
        workflow_id: int,
        new_name: str,
        created_by: str
    ) -> Optional[Workflow]:
        """
        Clone a workflow.

        Args:
            workflow_id: Source workflow ID
            new_name: Name for the cloned workflow
            created_by: User creating the clone

        Returns:
            Cloned workflow if source found, None otherwise
        """
        source = await self.get_workflow(workflow_id)
        if not source:
            return None

        # Create new workflow
        workflow = Workflow(
            name=new_name,
            description=source.description,
            version="1.0.0",
            definition=source.definition,
            is_template=False,
            timeout_seconds=source.timeout_seconds,
            tags=source.tags,
            metadata={**source.metadata, "cloned_from": workflow_id},
            created_by=created_by,
            status=WorkflowStatus.DRAFT,
        )
        self.db.add(workflow)
        await self.db.flush()

        # Clone tasks
        task_id_map = {}
        for task in source.tasks:
            new_task = Task(
                workflow_id=workflow.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type,
                config=task.config,
                depends_on=[],  # Will update after all tasks created
                retry_policy=task.retry_policy,
                timeout_seconds=task.timeout_seconds,
                priority=task.priority,
                metadata=task.metadata,
            )
            self.db.add(new_task)
            await self.db.flush()
            task_id_map[task.id] = new_task.id

        # Update dependencies with new task IDs
        for task in source.tasks:
            if task.depends_on:
                new_task_id = task_id_map[task.id]
                new_depends_on = [task_id_map[dep_id] for dep_id in task.depends_on if dep_id in task_id_map]
                await self.db.execute(
                    select(Task).where(Task.id == new_task_id)
                )
                # Update the task's depends_on
                task_to_update = await self.db.get(Task, new_task_id)
                if task_to_update:
                    task_to_update.depends_on = new_depends_on

        await self.db.commit()
        await self.db.refresh(workflow)

        logger.info(
            f"Cloned workflow {workflow_id} to {workflow.id}",
            extra={"source_id": workflow_id, "clone_id": workflow.id}
        )

        return workflow

    async def create_execution(
        self,
        workflow_id: int,
        execution_data: WorkflowExecutionCreate
    ) -> Optional[WorkflowExecution]:
        """
        Create a new workflow execution.

        Args:
            workflow_id: Workflow ID
            execution_data: Execution creation data

        Returns:
            Created execution if workflow found, None otherwise
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None

        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Cannot execute workflow with status: {workflow.status}")

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=ExecutionStatus.PENDING,
            triggered_by=execution_data.triggered_by,
            input_data=execution_data.input_data,
            correlation_id=str(uuid.uuid4()),
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        logger.info(
            f"Created execution for workflow {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "execution_id": execution.id,
                "correlation_id": execution.correlation_id
            }
        )

        return execution

    async def get_execution(
        self,
        execution_id: int
    ) -> Optional[WorkflowExecution]:
        """
        Get a workflow execution by ID.

        Args:
            execution_id: Execution ID

        Returns:
            Execution if found, None otherwise
        """
        query = (
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.task_executions))
            .where(WorkflowExecution.id == execution_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_executions(
        self,
        workflow_id: Optional[int],
        pagination: PaginationParams,
        status: Optional[ExecutionStatus] = None,
        triggered_by: Optional[str] = None,
    ) -> tuple[list[WorkflowExecution], int]:
        """
        List workflow executions with filtering and pagination.

        Args:
            workflow_id: Filter by workflow ID
            pagination: Pagination parameters
            status: Filter by status
            triggered_by: Filter by triggerer

        Returns:
            Tuple of executions list and total count
        """
        query = select(WorkflowExecution)
        count_query = select(func.count(WorkflowExecution.id))

        # Apply filters
        filters = []
        if workflow_id:
            filters.append(WorkflowExecution.workflow_id == workflow_id)
        if status:
            filters.append(WorkflowExecution.status == status)
        if triggered_by:
            filters.append(WorkflowExecution.triggered_by == triggered_by)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination
        offset = (pagination.page - 1) * pagination.page_size
        query = (
            query
            .order_by(WorkflowExecution.started_at.desc().nullslast())
            .offset(offset)
            .limit(pagination.page_size)
        )

        result = await self.db.execute(query)
        executions = result.scalars().all()

        return list(executions), total

    async def update_execution_status(
        self,
        execution_id: int,
        status: ExecutionStatus,
        error_message: Optional[str] = None,
        output_data: Optional[dict] = None
    ) -> Optional[WorkflowExecution]:
        """
        Update execution status.

        Args:
            execution_id: Execution ID
            status: New status
            error_message: Error message if failed
            output_data: Output data if completed

        Returns:
            Updated execution if found, None otherwise
        """
        execution = await self.get_execution(execution_id)
        if not execution:
            return None

        execution.status = status

        if status == ExecutionStatus.RUNNING and not execution.started_at:
            execution.started_at = datetime.utcnow()

        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                execution.metrics["duration_seconds"] = duration

        if error_message:
            execution.error_message = error_message

        if output_data:
            execution.output_data = output_data

        await self.db.commit()
        await self.db.refresh(execution)

        logger.info(
            f"Updated execution {execution_id} status to {status}",
            extra={"execution_id": execution_id, "status": status}
        )

        return execution

    async def cancel_execution(self, execution_id: int) -> Optional[WorkflowExecution]:
        """
        Cancel a running execution.

        Args:
            execution_id: Execution ID

        Returns:
            Cancelled execution if found, None otherwise
        """
        return await self.update_execution_status(
            execution_id,
            ExecutionStatus.CANCELLED,
            error_message="Execution cancelled by user"
        )

    async def get_workflow_statistics(
        self,
        created_by: Optional[str] = None
    ) -> dict:
        """
        Get workflow statistics.

        Args:
            created_by: Filter by creator

        Returns:
            Statistics dictionary
        """
        # Total workflows by status
        query = select(
            Workflow.status,
            func.count(Workflow.id)
        ).group_by(Workflow.status)

        if created_by:
            query = query.where(Workflow.created_by == created_by)

        result = await self.db.execute(query)
        status_counts = dict(result.all())

        # Execution statistics
        exec_query = select(
            WorkflowExecution.status,
            func.count(WorkflowExecution.id)
        ).group_by(WorkflowExecution.status)

        exec_result = await self.db.execute(exec_query)
        exec_status_counts = dict(exec_result.all())

        # Average execution duration
        duration_query = select(
            func.avg(
                func.extract(
                    'epoch',
                    WorkflowExecution.completed_at - WorkflowExecution.started_at
                )
            )
        ).where(WorkflowExecution.completed_at.isnot(None))

        duration_result = await self.db.execute(duration_query)
        avg_duration = duration_result.scalar() or 0

        total_workflows = sum(status_counts.values())
        total_executions = sum(exec_status_counts.values())
        successful = exec_status_counts.get(ExecutionStatus.COMPLETED, 0)
        failed = exec_status_counts.get(ExecutionStatus.FAILED, 0)

        return {
            "total_workflows": total_workflows,
            "active_workflows": status_counts.get(WorkflowStatus.ACTIVE, 0),
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": failed,
            "average_duration_seconds": round(avg_duration, 2),
            "success_rate": round(successful / total_executions, 2) if total_executions > 0 else 0,
        }
