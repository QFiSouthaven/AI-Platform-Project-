"""
Execution API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workflow import ExecutionStatus
from app.models.task import TaskStatus
from app.models.schemas import (
    WorkflowExecutionResponse,
    WorkflowExecutionListResponse,
    TaskExecutionResponse,
    PaginationParams,
    PaginatedResponse,
    APIResponse,
)
from app.services.workflow_service import WorkflowService
from app.services.task_service import TaskService
from app.services.orchestrator import WorkflowOrchestrator
from app.kafka.producer import get_kafka_producer, KafkaProducer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    workflow_id: Optional[int] = None,
    status: Optional[ExecutionStatus] = None,
    triggered_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all workflow executions with filtering.
    """
    service = WorkflowService(db)
    pagination = PaginationParams(page=page, page_size=page_size)

    executions, total = await service.list_executions(
        workflow_id,
        pagination,
        status=status,
        triggered_by=triggered_by
    )

    items = [
        WorkflowExecutionListResponse(
            id=exec.id,
            workflow_id=exec.workflow_id,
            status=exec.status,
            started_at=exec.started_at,
            completed_at=exec.completed_at,
            triggered_by=exec.triggered_by,
            correlation_id=exec.correlation_id,
            metrics=exec.metrics
        )
        for exec in executions
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{execution_id}", response_model=APIResponse)
async def get_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a workflow execution by ID.
    """
    service = WorkflowService(db)
    execution = await service.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return APIResponse(
        status="success",
        data=WorkflowExecutionResponse.model_validate(execution)
    )


@router.post("/{execution_id}/cancel", response_model=APIResponse)
async def cancel_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer)
):
    """
    Cancel a running workflow execution.
    """
    orchestrator = WorkflowOrchestrator(db, kafka_producer)
    cancelled = await orchestrator.cancel_execution(execution_id)

    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel execution. It may not exist or is not running."
        )

    execution = await WorkflowService(db).get_execution(execution_id)

    return APIResponse(
        status="success",
        data=WorkflowExecutionResponse.model_validate(execution),
        message="Execution cancelled successfully"
    )


@router.post("/{execution_id}/retry", response_model=APIResponse)
async def retry_execution(
    execution_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer)
):
    """
    Retry a failed workflow execution.
    """
    orchestrator = WorkflowOrchestrator(db, kafka_producer)
    new_execution_id = await orchestrator.retry_execution(execution_id)

    if not new_execution_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot retry execution. It may not exist or is not in failed state."
        )

    # Get original execution for workflow_id
    original = await WorkflowService(db).get_execution(execution_id)

    # Start new execution in background
    background_tasks.add_task(
        orchestrator.start_execution,
        original.workflow_id,
        new_execution_id
    )

    new_execution = await WorkflowService(db).get_execution(new_execution_id)

    return APIResponse(
        status="success",
        data=WorkflowExecutionResponse.model_validate(new_execution),
        message=f"Execution retry started (new execution ID: {new_execution_id})"
    )


@router.get("/{execution_id}/tasks", response_model=PaginatedResponse)
async def list_execution_tasks(
    execution_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List task executions for a workflow execution.
    """
    # Verify execution exists
    workflow_service = WorkflowService(db)
    execution = await workflow_service.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    task_service = TaskService(db)
    pagination = PaginationParams(page=page, page_size=page_size)

    task_executions, total = await task_service.list_task_executions(
        execution_id,
        pagination,
        status=status
    )

    items = [
        TaskExecutionResponse.model_validate(exec)
        for exec in task_executions
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{execution_id}/tasks/{task_execution_id}", response_model=APIResponse)
async def get_task_execution(
    execution_id: int,
    task_execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific task execution.
    """
    task_service = TaskService(db)
    task_execution = await task_service.get_task_execution(task_execution_id)

    if not task_execution or task_execution.workflow_execution_id != execution_id:
        raise HTTPException(status_code=404, detail="Task execution not found")

    return APIResponse(
        status="success",
        data=TaskExecutionResponse.model_validate(task_execution)
    )


@router.get("/{execution_id}/logs", response_model=APIResponse)
async def get_execution_logs(
    execution_id: int,
    task_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get logs for a workflow execution.
    """
    workflow_service = WorkflowService(db)
    execution = await workflow_service.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = []
    for task_exec in execution.task_executions:
        if task_id and task_exec.task_id != task_id:
            continue

        logs.extend([
            {
                "task_execution_id": task_exec.id,
                "task_id": task_exec.task_id,
                **log
            }
            for log in task_exec.logs
        ])

    # Sort by timestamp if available
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return APIResponse(
        status="success",
        data=logs
    )


@router.get("/{execution_id}/metrics", response_model=APIResponse)
async def get_execution_metrics(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get metrics for a workflow execution.
    """
    workflow_service = WorkflowService(db)
    execution = await workflow_service.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Aggregate task metrics
    task_metrics = {}
    total_duration = 0
    completed_tasks = 0
    failed_tasks = 0

    for task_exec in execution.task_executions:
        task_metrics[task_exec.task_id] = task_exec.metrics

        if task_exec.status == TaskStatus.COMPLETED:
            completed_tasks += 1
        elif task_exec.status == TaskStatus.FAILED:
            failed_tasks += 1

        if "duration_seconds" in task_exec.metrics:
            total_duration += task_exec.metrics["duration_seconds"]

    metrics = {
        "execution_metrics": execution.metrics,
        "task_metrics": task_metrics,
        "summary": {
            "total_tasks": len(execution.task_executions),
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "total_task_duration_seconds": round(total_duration, 2),
            "execution_duration_seconds": execution.metrics.get("duration_seconds", 0)
        }
    }

    return APIResponse(
        status="success",
        data=metrics
    )
