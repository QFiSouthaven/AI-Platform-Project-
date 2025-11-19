"""
Workers API - Worker Management Endpoints

This module provides endpoints for managing and monitoring workers
in the distributed computing cluster.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

import structlog

from app.services.resource_manager import ResourceType

logger = structlog.get_logger(__name__)

router = APIRouter()


# Request/Response Models

class WorkerUpdateRequest(BaseModel):
    """Request model for updating worker status."""
    status: str = Field(..., description="New worker status")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Worker metrics")


class WorkerScaleRequest(BaseModel):
    """Request model for scaling workers."""
    target_count: int = Field(..., ge=1, description="Target number of workers")


class WorkerResponse(BaseModel):
    """Response model for worker information."""
    worker_id: str
    status: str
    created_at: str
    cpu_allocated: float
    memory_allocated_mb: int
    metrics: Optional[Dict[str, Any]] = None


@router.get("/", response_model=Dict[str, Any])
async def list_workers(
    request: Request,
    status: Optional[str] = Query(default=None, description="Filter by worker status")
):
    """
    List all workers in the cluster.
    """
    resource_manager = request.app.state.resource_manager

    try:
        workers = await resource_manager.get_all_workers()

        # Filter by status if provided
        if status:
            workers = [w for w in workers if w.get("status") == status]

        return {
            "status": "success",
            "data": {
                "workers": workers,
                "total": len(workers)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to list workers", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "WORKER_LIST_FAILED",
                "message": str(e)
            }
        )


@router.get("/{worker_id}", response_model=Dict[str, Any])
async def get_worker(request: Request, worker_id: str):
    """
    Get information about a specific worker.
    """
    resource_manager = request.app.state.resource_manager

    try:
        worker = await resource_manager.get_worker(worker_id)

        if not worker:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "WORKER_NOT_FOUND",
                    "message": f"Worker {worker_id} not found"
                }
            )

        return {
            "status": "success",
            "data": worker,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get worker", worker_id=worker_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "WORKER_GET_FAILED",
                "message": str(e)
            }
        )


@router.patch("/{worker_id}", response_model=Dict[str, Any])
async def update_worker(
    request: Request,
    worker_id: str,
    update_request: WorkerUpdateRequest
):
    """
    Update worker status and metrics.
    """
    resource_manager = request.app.state.resource_manager

    try:
        updated = await resource_manager.update_worker_status(
            worker_id=worker_id,
            status=update_request.status,
            metrics=update_request.metrics
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "WORKER_NOT_FOUND",
                    "message": f"Worker {worker_id} not found"
                }
            )

        worker = await resource_manager.get_worker(worker_id)

        return {
            "status": "success",
            "data": worker,
            "message": "Worker updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update worker", worker_id=worker_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "WORKER_UPDATE_FAILED",
                "message": str(e)
            }
        )


@router.post("/scale", response_model=Dict[str, Any])
async def scale_workers(request: Request, scale_request: WorkerScaleRequest):
    """
    Scale the number of workers to a target count.
    """
    resource_manager = request.app.state.resource_manager
    autoscaler = request.app.state.autoscaler

    try:
        result = await autoscaler.trigger_manual_scale(scale_request.target_count)

        return {
            "status": "success",
            "data": result,
            "message": f"Workers scaled to {scale_request.target_count}",
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SCALE_REQUEST",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error("Failed to scale workers", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "WORKER_SCALE_FAILED",
                "message": str(e)
            }
        )


@router.get("/nodes/list", response_model=Dict[str, Any])
async def list_nodes(request: Request):
    """
    List all nodes in the Ray cluster.
    """
    ray_service = request.app.state.ray_service

    try:
        nodes = await ray_service.get_nodes()

        return {
            "status": "success",
            "data": {
                "nodes": nodes,
                "total": len(nodes),
                "alive": len([n for n in nodes if n.get("alive")])
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to list nodes", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "NODE_LIST_FAILED",
                "message": str(e)
            }
        )


@router.get("/resources", response_model=Dict[str, Any])
async def get_cluster_resources(request: Request):
    """
    Get current cluster resource usage and availability.
    """
    ray_service = request.app.state.ray_service

    try:
        resources = await ray_service.get_cluster_resources()

        return {
            "status": "success",
            "data": resources,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get cluster resources", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "RESOURCE_GET_FAILED",
                "message": str(e)
            }
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_worker_stats(request: Request):
    """
    Get worker statistics summary.
    """
    resource_manager = request.app.state.resource_manager

    try:
        stats = await resource_manager.get_resource_stats()

        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get worker stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "WORKER_STATS_FAILED",
                "message": str(e)
            }
        )


@router.get("/health/all", response_model=Dict[str, Any])
async def get_all_workers_health(request: Request):
    """
    Get health status of all workers.
    """
    health_monitor = request.app.state.health_monitor

    try:
        components = await health_monitor.get_all_components_health()
        worker_health = [c for c in components if c.get("component_type") == "node"]

        return {
            "status": "success",
            "data": {
                "workers": worker_health,
                "total": len(worker_health),
                "healthy": len([w for w in worker_health if w.get("status") == "healthy"])
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get workers health", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "WORKER_HEALTH_FAILED",
                "message": str(e)
            }
        )
