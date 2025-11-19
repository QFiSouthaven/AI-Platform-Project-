"""
Task API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.task import TaskStatus
from app.models.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskExecutionResponse,
    PaginationParams,
    PaginatedResponse,
    APIResponse,
    TaskStatistics,
)
from app.services.task_service import TaskService
from app.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=APIResponse)
async def create_task(
    task_data: TaskCreate,
    workflow_id: int = Query(..., description="Workflow to add the task to"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new task for a workflow.
    """
    # Verify workflow exists
    workflow_service = WorkflowService(db)
    workflow = await workflow_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    task_service = TaskService(db)
    task = await task_service.create_task(workflow_id, task_data)

    return APIResponse(
        status="success",
        data=TaskResponse.model_validate(task),
        message=f"Task '{task.name}' created successfully"
    )


@router.get("", response_model=PaginatedResponse)
async def list_tasks(
    workflow_id: int = Query(..., description="Workflow ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List tasks for a workflow.
    """
    task_service = TaskService(db)
    pagination = PaginationParams(page=page, page_size=page_size)

    tasks, total = await task_service.list_tasks(workflow_id, pagination)

    items = [TaskResponse.model_validate(task) for task in tasks]
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/statistics", response_model=APIResponse)
async def get_task_statistics(
    workflow_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get task statistics.
    """
    task_service = TaskService(db)
    stats = await task_service.get_task_statistics(workflow_id)

    return APIResponse(
        status="success",
        data=TaskStatistics(**stats)
    )


@router.get("/{task_id}", response_model=APIResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a task by ID.
    """
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(
        status="success",
        data=TaskResponse.model_validate(task)
    )


@router.put("/{task_id}", response_model=APIResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a task.
    """
    task_service = TaskService(db)
    task = await task_service.update_task(task_id, task_data)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(
        status="success",
        data=TaskResponse.model_validate(task),
        message="Task updated successfully"
    )


@router.delete("/{task_id}", response_model=APIResponse)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a task.
    """
    task_service = TaskService(db)
    deleted = await task_service.delete_task(task_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(
        status="success",
        message=f"Task {task_id} deleted successfully"
    )


@router.get("/{task_id}/executions", response_model=PaginatedResponse)
async def list_task_executions(
    task_id: int,
    workflow_execution_id: int = Query(..., description="Workflow execution ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List executions for a specific task.
    """
    task_service = TaskService(db)

    # Verify task exists
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    pagination = PaginationParams(page=page, page_size=page_size)
    executions, total = await task_service.list_task_executions(
        workflow_execution_id,
        pagination,
        status=status
    )

    # Filter by task_id
    executions = [e for e in executions if e.task_id == task_id]

    items = [TaskExecutionResponse.model_validate(exec) for exec in executions]
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=len(items),
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
