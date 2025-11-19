"""
Tasks API - Distributed Task Submission and Management

This module provides endpoints for submitting, monitoring, and managing
distributed tasks executed on the Ray cluster.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

import structlog

from app.services.ray_service import TaskStatus

logger = structlog.get_logger(__name__)

router = APIRouter()


# Request/Response Models

class TaskSubmitRequest(BaseModel):
    """Request model for task submission."""
    task_type: str = Field(..., description="Type of task to execute")
    payload: Dict[str, Any] = Field(default={}, description="Task payload data")
    priority: int = Field(default=1, ge=1, le=10, description="Task priority (1-10)")
    timeout: Optional[int] = Field(default=None, description="Task timeout in seconds")
    max_retries: Optional[int] = Field(default=None, description="Maximum retry attempts")
    num_cpus: Optional[float] = Field(default=None, description="CPUs to allocate")
    num_gpus: Optional[float] = Field(default=None, description="GPUs to allocate")
    memory_mb: Optional[int] = Field(default=None, description="Memory in MB to allocate")


class TaskResponse(BaseModel):
    """Response model for task information."""
    task_id: str
    status: str
    submitted_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


# Sample task functions for demonstration
def sample_compute_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sample compute task for testing."""
    import time
    time.sleep(data.get("duration", 1))
    return {
        "input": data,
        "result": "computed",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/submit", response_model=Dict[str, Any])
async def submit_task(request: Request, task_request: TaskSubmitRequest):
    """
    Submit a new task for distributed execution.

    The task will be queued and executed on an available worker in the Ray cluster.
    """
    ray_service = request.app.state.ray_service
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    try:
        task_id = str(uuid.uuid4())

        # Convert memory from MB to bytes if specified
        memory_bytes = None
        if task_request.memory_mb:
            memory_bytes = task_request.memory_mb * 1024 * 1024

        # Submit the task
        await ray_service.submit_task(
            task_id=task_id,
            func=sample_compute_task,
            args=(task_request.payload,),
            num_cpus=task_request.num_cpus,
            num_gpus=task_request.num_gpus,
            memory=memory_bytes,
            timeout=task_request.timeout,
            max_retries=task_request.max_retries
        )

        logger.info(
            "Task submitted",
            task_id=task_id,
            task_type=task_request.task_type,
            correlation_id=correlation_id
        )

        return {
            "status": "success",
            "data": {
                "task_id": task_id,
                "status": "submitted",
                "task_type": task_request.task_type
            },
            "message": "Task submitted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(
            "Failed to submit task",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_SUBMISSION_FAILED",
                "message": str(e)
            }
        )


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(request: Request, task_id: str):
    """
    Get the status and result of a submitted task.
    """
    ray_service = request.app.state.ray_service

    try:
        status = await ray_service.get_task_status(task_id)

        if status.get("status") == "not_found":
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task {task_id} not found"
                }
            )

        return {
            "status": "success",
            "data": status,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_STATUS_FAILED",
                "message": str(e)
            }
        )


@router.get("/{task_id}/result", response_model=Dict[str, Any])
async def get_task_result(
    request: Request,
    task_id: str,
    timeout: int = Query(default=30, description="Timeout in seconds to wait for result")
):
    """
    Get the result of a completed task.

    This will wait up to the specified timeout for the task to complete.
    """
    ray_service = request.app.state.ray_service

    try:
        result = await ray_service.get_task_result(task_id, timeout=timeout)

        return {
            "status": "success",
            "data": result.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get task result", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_RESULT_FAILED",
                "message": str(e)
            }
        )


@router.post("/{task_id}/cancel", response_model=Dict[str, Any])
async def cancel_task(request: Request, task_id: str):
    """
    Cancel a running task.
    """
    ray_service = request.app.state.ray_service

    try:
        cancelled = await ray_service.cancel_task(task_id)

        if not cancelled:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task {task_id} not found or already completed"
                }
            )

        logger.info("Task cancelled", task_id=task_id)

        return {
            "status": "success",
            "data": {
                "task_id": task_id,
                "cancelled": True
            },
            "message": "Task cancelled successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_CANCEL_FAILED",
                "message": str(e)
            }
        )


@router.get("/", response_model=Dict[str, Any])
async def list_tasks(
    request: Request,
    status: Optional[str] = Query(default=None, description="Filter by task status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum tasks to return"),
    page: int = Query(default=1, ge=1, description="Page number")
):
    """
    List all tasks with optional filtering.
    """
    ray_service = request.app.state.ray_service

    try:
        # Convert status string to enum if provided
        task_status = None
        if status:
            try:
                task_status = TaskStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_STATUS",
                        "message": f"Invalid status: {status}"
                    }
                )

        tasks = await ray_service.list_tasks(status=task_status, limit=limit)

        # Simple pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_tasks = tasks[start_idx:end_idx]

        return {
            "status": "success",
            "data": {
                "tasks": paginated_tasks,
                "total": len(tasks),
                "page": page,
                "page_size": limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list tasks", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_LIST_FAILED",
                "message": str(e)
            }
        )


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_tasks(
    request: Request,
    max_age_hours: int = Query(default=1, description="Maximum age of completed tasks to keep")
):
    """
    Clean up old completed tasks.
    """
    ray_service = request.app.state.ray_service

    try:
        max_age_seconds = max_age_hours * 3600
        removed = await ray_service.cleanup_completed_tasks(max_age_seconds)

        return {
            "status": "success",
            "data": {
                "removed_tasks": removed,
                "max_age_hours": max_age_hours
            },
            "message": f"Cleaned up {removed} completed tasks",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to cleanup tasks", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_CLEANUP_FAILED",
                "message": str(e)
            }
        )


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_task_stats(request: Request):
    """
    Get task execution statistics.
    """
    ray_service = request.app.state.ray_service

    try:
        tasks = await ray_service.list_tasks(limit=10000)

        # Calculate statistics
        total = len(tasks)
        by_status = {}
        for task in tasks:
            status = task.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "status": "success",
            "data": {
                "total_tasks": total,
                "by_status": by_status
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get task stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_STATS_FAILED",
                "message": str(e)
            }
        )
