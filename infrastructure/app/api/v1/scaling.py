"""
Scaling API - Auto-scaling Configuration Endpoints

This module provides endpoints for configuring and managing
the auto-scaling behavior of the infrastructure.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


# Request/Response Models

class ScalingConfigUpdate(BaseModel):
    """Request model for updating scaling configuration."""
    min_workers: Optional[int] = Field(default=None, ge=1, description="Minimum number of workers")
    max_workers: Optional[int] = Field(default=None, ge=1, description="Maximum number of workers")
    cpu_threshold_high: Optional[float] = Field(default=None, ge=0, le=100, description="CPU high threshold")
    cpu_threshold_low: Optional[float] = Field(default=None, ge=0, le=100, description="CPU low threshold")
    memory_threshold_high: Optional[float] = Field(default=None, ge=0, le=100, description="Memory high threshold")
    memory_threshold_low: Optional[float] = Field(default=None, ge=0, le=100, description="Memory low threshold")
    queue_threshold: Optional[int] = Field(default=None, ge=1, description="Queue depth threshold")
    cooldown_period: Optional[int] = Field(default=None, ge=0, description="Cooldown period in seconds")
    scale_up_increment: Optional[int] = Field(default=None, ge=1, description="Workers to add when scaling up")
    scale_down_increment: Optional[int] = Field(default=None, ge=1, description="Workers to remove when scaling down")


class ScalingStateResponse(BaseModel):
    """Response model for scaling state."""
    enabled: bool
    current_workers: int
    in_cooldown: bool
    cooldown_remaining_seconds: int
    last_scale_action: Optional[str]
    current_metrics: Dict[str, Any]


@router.get("/config", response_model=Dict[str, Any])
async def get_scaling_config(request: Request):
    """
    Get current auto-scaling configuration.
    """
    autoscaler = request.app.state.autoscaler

    try:
        config = await autoscaler.get_config()

        return {
            "status": "success",
            "data": config,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get scaling config", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONFIG_GET_FAILED",
                "message": str(e)
            }
        )


@router.patch("/config", response_model=Dict[str, Any])
async def update_scaling_config(request: Request, config_update: ScalingConfigUpdate):
    """
    Update auto-scaling configuration.
    """
    autoscaler = request.app.state.autoscaler

    try:
        # Validate thresholds
        if config_update.cpu_threshold_low and config_update.cpu_threshold_high:
            if config_update.cpu_threshold_low >= config_update.cpu_threshold_high:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_THRESHOLDS",
                        "message": "CPU low threshold must be less than high threshold"
                    }
                )

        if config_update.memory_threshold_low and config_update.memory_threshold_high:
            if config_update.memory_threshold_low >= config_update.memory_threshold_high:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_THRESHOLDS",
                        "message": "Memory low threshold must be less than high threshold"
                    }
                )

        if config_update.min_workers and config_update.max_workers:
            if config_update.min_workers > config_update.max_workers:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "INVALID_WORKERS",
                        "message": "Min workers cannot be greater than max workers"
                    }
                )

        updated_config = await autoscaler.update_config(
            min_workers=config_update.min_workers,
            max_workers=config_update.max_workers,
            cpu_threshold_high=config_update.cpu_threshold_high,
            cpu_threshold_low=config_update.cpu_threshold_low,
            memory_threshold_high=config_update.memory_threshold_high,
            memory_threshold_low=config_update.memory_threshold_low,
            queue_threshold=config_update.queue_threshold,
            cooldown_period=config_update.cooldown_period,
            scale_up_increment=config_update.scale_up_increment,
            scale_down_increment=config_update.scale_down_increment
        )

        logger.info("Scaling configuration updated")

        return {
            "status": "success",
            "data": updated_config,
            "message": "Scaling configuration updated",
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update scaling config", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CONFIG_UPDATE_FAILED",
                "message": str(e)
            }
        )


@router.get("/state", response_model=Dict[str, Any])
async def get_scaling_state(request: Request):
    """
    Get current auto-scaling state.
    """
    autoscaler = request.app.state.autoscaler

    try:
        state = await autoscaler.get_current_state()

        return {
            "status": "success",
            "data": state,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get scaling state", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATE_GET_FAILED",
                "message": str(e)
            }
        )


@router.post("/enable", response_model=Dict[str, Any])
async def enable_autoscaling(request: Request):
    """
    Enable auto-scaling.
    """
    autoscaler = request.app.state.autoscaler

    try:
        await autoscaler.set_enabled(True)

        return {
            "status": "success",
            "data": {
                "enabled": True
            },
            "message": "Auto-scaling enabled",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to enable autoscaling", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ENABLE_FAILED",
                "message": str(e)
            }
        )


@router.post("/disable", response_model=Dict[str, Any])
async def disable_autoscaling(request: Request):
    """
    Disable auto-scaling.
    """
    autoscaler = request.app.state.autoscaler

    try:
        await autoscaler.set_enabled(False)

        return {
            "status": "success",
            "data": {
                "enabled": False
            },
            "message": "Auto-scaling disabled",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to disable autoscaling", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DISABLE_FAILED",
                "message": str(e)
            }
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_scaling_history(request: Request):
    """
    Get scaling action history.
    """
    autoscaler = request.app.state.autoscaler

    try:
        history = await autoscaler.get_scaling_history()

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
                "code": "HISTORY_GET_FAILED",
                "message": str(e)
            }
        )


@router.post("/trigger", response_model=Dict[str, Any])
async def trigger_manual_scale(
    request: Request,
    target_workers: int
):
    """
    Manually trigger scaling to a specific number of workers.

    This bypasses the automatic scaling logic and immediately
    scales to the target number of workers.
    """
    autoscaler = request.app.state.autoscaler

    try:
        result = await autoscaler.trigger_manual_scale(target_workers)

        return {
            "status": "success",
            "data": result,
            "message": f"Manually scaled to {target_workers} workers",
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_TARGET",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error("Failed to trigger manual scale", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SCALE_TRIGGER_FAILED",
                "message": str(e)
            }
        )


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_scaling_recommendations(request: Request):
    """
    Get recommendations for scaling configuration based on current usage.
    """
    autoscaler = request.app.state.autoscaler
    ray_service = request.app.state.ray_service

    try:
        state = await autoscaler.get_current_state()
        config = await autoscaler.get_config()
        metrics = state.get("current_metrics", {})

        recommendations = []

        # Analyze CPU usage
        cpu_usage = metrics.get("cpu_usage_percent", 0)
        if cpu_usage > 90:
            recommendations.append({
                "type": "warning",
                "message": f"CPU usage is very high ({cpu_usage:.1f}%). Consider increasing max_workers.",
                "current_value": config.get("max_workers"),
                "suggested_value": config.get("max_workers", 10) + 5
            })
        elif cpu_usage < 10 and state.get("current_workers", 1) > config.get("min_workers", 1):
            recommendations.append({
                "type": "info",
                "message": f"CPU usage is very low ({cpu_usage:.1f}%). Consider decreasing min_workers.",
                "current_value": config.get("min_workers"),
                "suggested_value": max(1, config.get("min_workers", 1) - 1)
            })

        # Analyze memory usage
        memory_usage = metrics.get("memory_usage_percent", 0)
        if memory_usage > 90:
            recommendations.append({
                "type": "warning",
                "message": f"Memory usage is very high ({memory_usage:.1f}%). Consider adding more workers.",
                "action": "scale_up"
            })

        # Analyze queue depth
        pending_tasks = metrics.get("pending_tasks", 0)
        if pending_tasks > config.get("queue_threshold", 100) * 2:
            recommendations.append({
                "type": "warning",
                "message": f"Queue depth ({pending_tasks}) is very high. Consider increasing queue_threshold or max_workers.",
                "current_value": config.get("queue_threshold"),
                "suggested_value": pending_tasks + 50
            })

        # Check if autoscaling is disabled
        if not state.get("enabled"):
            recommendations.append({
                "type": "info",
                "message": "Auto-scaling is disabled. Enable it for automatic resource management."
            })

        return {
            "status": "success",
            "data": {
                "recommendations": recommendations,
                "count": len(recommendations),
                "current_metrics": metrics
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get scaling recommendations", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "RECOMMENDATIONS_FAILED",
                "message": str(e)
            }
        )
