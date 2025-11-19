"""
Metrics API - Performance Metrics Endpoints

This module provides endpoints for retrieving performance metrics,
resource usage, and operational statistics.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


# Request/Response Models

class MetricsQueryParams(BaseModel):
    """Query parameters for metrics retrieval."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interval: str = "1m"  # 1m, 5m, 1h, 1d


@router.get("/cluster", response_model=Dict[str, Any])
async def get_cluster_metrics(request: Request):
    """
    Get current cluster-wide metrics.
    """
    ray_service = request.app.state.ray_service
    health_monitor = request.app.state.health_monitor
    autoscaler = request.app.state.autoscaler

    try:
        resources = await ray_service.get_cluster_resources()
        health = await health_monitor.get_cluster_health()
        scaling_state = await autoscaler.get_current_state()

        total = resources.get("total", {})
        available = resources.get("available", {})

        # Calculate utilization percentages
        cpu_total = total.get("cpus", 1)
        cpu_used = cpu_total - available.get("cpus", 0)
        cpu_utilization = (cpu_used / cpu_total * 100) if cpu_total > 0 else 0

        memory_total = total.get("memory_bytes", 1)
        memory_used = memory_total - available.get("memory_bytes", 0)
        memory_utilization = (memory_used / memory_total * 100) if memory_total > 0 else 0

        return {
            "status": "success",
            "data": {
                "cpu": {
                    "total": cpu_total,
                    "used": cpu_used,
                    "available": available.get("cpus", 0),
                    "utilization_percent": round(cpu_utilization, 2)
                },
                "memory": {
                    "total_bytes": memory_total,
                    "used_bytes": memory_used,
                    "available_bytes": available.get("memory_bytes", 0),
                    "utilization_percent": round(memory_utilization, 2)
                },
                "gpu": {
                    "total": total.get("gpus", 0),
                    "available": available.get("gpus", 0)
                },
                "health": health,
                "scaling": scaling_state,
                "uptime_seconds": health_monitor.get_uptime()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get cluster metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "METRICS_FAILED",
                "message": str(e)
            }
        )


@router.get("/tasks", response_model=Dict[str, Any])
async def get_task_metrics(request: Request):
    """
    Get task execution metrics.
    """
    ray_service = request.app.state.ray_service

    try:
        tasks = await ray_service.list_tasks(limit=10000)

        # Calculate task metrics
        total = len(tasks)
        by_status = {}
        for task in tasks:
            status = task.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        pending = by_status.get("pending", 0)
        running = by_status.get("running", 0)
        completed = by_status.get("completed", 0)
        failed = by_status.get("failed", 0)

        success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0

        return {
            "status": "success",
            "data": {
                "total_tasks": total,
                "by_status": by_status,
                "pending": pending,
                "running": running,
                "completed": completed,
                "failed": failed,
                "success_rate_percent": round(success_rate, 2),
                "queue_depth": pending + running
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get task metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TASK_METRICS_FAILED",
                "message": str(e)
            }
        )


@router.get("/resources", response_model=Dict[str, Any])
async def get_resource_metrics(request: Request):
    """
    Get resource allocation metrics.
    """
    resource_manager = request.app.state.resource_manager

    try:
        availability = await resource_manager.get_resource_availability()
        stats = await resource_manager.get_resource_stats()

        return {
            "status": "success",
            "data": {
                "availability": availability,
                "reservations": {
                    "total": stats.get("total_reservations", 0),
                    "active": stats.get("active_reservations", 0)
                },
                "workers": {
                    "total": stats.get("total_workers", 0),
                    "by_status": stats.get("workers_by_status", {})
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get resource metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "RESOURCE_METRICS_FAILED",
                "message": str(e)
            }
        )


@router.get("/health/history", response_model=Dict[str, Any])
async def get_health_history(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
    hours: int = Query(default=1, ge=1, le=24, description="Hours of history to retrieve")
):
    """
    Get historical health metrics.
    """
    health_monitor = request.app.state.health_monitor

    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        history = await health_monitor.get_health_history(limit=limit, since=since)

        return {
            "status": "success",
            "data": {
                "history": history,
                "count": len(history),
                "period_hours": hours
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get health history", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "HEALTH_HISTORY_FAILED",
                "message": str(e)
            }
        )


@router.get("/scaling/history", response_model=Dict[str, Any])
async def get_scaling_history(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum records to return")
):
    """
    Get scaling action history.
    """
    autoscaler = request.app.state.autoscaler

    try:
        history = await autoscaler.get_scaling_history(limit=limit)

        return {
            "status": "success",
            "data": {
                "history": history,
                "count": len(history)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get scaling history", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SCALING_HISTORY_FAILED",
                "message": str(e)
            }
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts(
    request: Request,
    severity: Optional[str] = Query(default=None, description="Filter by severity"),
    acknowledged: Optional[bool] = Query(default=None, description="Filter by acknowledged status"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum alerts to return")
):
    """
    Get health alerts.
    """
    health_monitor = request.app.state.health_monitor

    try:
        alerts = await health_monitor.get_alerts(
            severity=severity,
            acknowledged=acknowledged,
            limit=limit
        )

        return {
            "status": "success",
            "data": {
                "alerts": alerts,
                "count": len(alerts),
                "unacknowledged": len([a for a in alerts if not a.get("acknowledged")])
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get alerts", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ALERTS_FAILED",
                "message": str(e)
            }
        )


@router.post("/alerts/{alert_index}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(request: Request, alert_index: int):
    """
    Acknowledge an alert.
    """
    health_monitor = request.app.state.health_monitor

    try:
        acknowledged = await health_monitor.acknowledge_alert(alert_index)

        if not acknowledged:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ALERT_NOT_FOUND",
                    "message": f"Alert at index {alert_index} not found"
                }
            )

        return {
            "status": "success",
            "data": {
                "acknowledged": True,
                "alert_index": alert_index
            },
            "message": "Alert acknowledged",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to acknowledge alert", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ACKNOWLEDGE_FAILED",
                "message": str(e)
            }
        )


@router.post("/alerts/clear", response_model=Dict[str, Any])
async def clear_acknowledged_alerts(request: Request):
    """
    Clear all acknowledged alerts.
    """
    health_monitor = request.app.state.health_monitor

    try:
        cleared = await health_monitor.clear_alerts()

        return {
            "status": "success",
            "data": {
                "cleared_count": cleared
            },
            "message": f"Cleared {cleared} acknowledged alerts",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to clear alerts", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CLEAR_ALERTS_FAILED",
                "message": str(e)
            }
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_metrics_summary(request: Request):
    """
    Get a summary of all key metrics.
    """
    ray_service = request.app.state.ray_service
    health_monitor = request.app.state.health_monitor
    autoscaler = request.app.state.autoscaler
    resource_manager = request.app.state.resource_manager

    try:
        # Gather all metrics
        resources = await ray_service.get_cluster_resources()
        health = await health_monitor.get_cluster_health()
        scaling_state = await autoscaler.get_current_state()
        resource_stats = await resource_manager.get_resource_stats()
        tasks = await ray_service.list_tasks(limit=10000)

        # Calculate task stats
        task_by_status = {}
        for task in tasks:
            status = task.get("status", "unknown")
            task_by_status[status] = task_by_status.get(status, 0) + 1

        return {
            "status": "success",
            "data": {
                "cluster": {
                    "health_status": health.get("status"),
                    "total_cpus": resources.get("total", {}).get("cpus", 0),
                    "available_cpus": resources.get("available", {}).get("cpus", 0),
                    "workers": scaling_state.get("current_workers", 0),
                    "uptime_seconds": health_monitor.get_uptime()
                },
                "tasks": {
                    "total": len(tasks),
                    "pending": task_by_status.get("pending", 0),
                    "running": task_by_status.get("running", 0),
                    "completed": task_by_status.get("completed", 0),
                    "failed": task_by_status.get("failed", 0)
                },
                "scaling": {
                    "enabled": scaling_state.get("enabled"),
                    "in_cooldown": scaling_state.get("in_cooldown"),
                    "current_workers": scaling_state.get("current_workers")
                },
                "resources": {
                    "total_workers": resource_stats.get("total_workers", 0),
                    "active_reservations": resource_stats.get("active_reservations", 0)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get metrics summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "METRICS_SUMMARY_FAILED",
                "message": str(e)
            }
        )
