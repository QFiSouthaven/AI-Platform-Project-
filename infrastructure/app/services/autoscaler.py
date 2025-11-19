"""
AutoScaler Service - Automatic Resource Scaling

This service monitors resource usage and automatically scales
workers up or down based on configurable thresholds.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class ScalingAction(str, Enum):
    """Types of scaling actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"
    COOLDOWN = "cooldown"


class ScalingDecision:
    """Represents a scaling decision."""

    def __init__(
        self,
        action: ScalingAction,
        reason: str,
        current_workers: int,
        target_workers: int,
        metrics: Dict[str, Any]
    ):
        self.action = action
        self.reason = reason
        self.current_workers = current_workers
        self.target_workers = target_workers
        self.metrics = metrics
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "reason": self.reason,
            "current_workers": self.current_workers,
            "target_workers": self.target_workers,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat()
        }


class AutoScaler:
    """
    Service for automatic scaling of workers based on resource usage.
    """

    def __init__(self, ray_service, resource_manager, health_monitor):
        self.ray_service = ray_service
        self.resource_manager = resource_manager
        self.health_monitor = health_monitor
        self._running = False
        self._scaler_task = None
        self._enabled = settings.AUTOSCALE_ENABLED
        self._last_scale_action: Optional[datetime] = None
        self._scaling_history: List[Dict[str, Any]] = []
        self._current_workers = settings.MIN_WORKERS

        # Configurable thresholds
        self._min_workers = settings.MIN_WORKERS
        self._max_workers = settings.MAX_WORKERS
        self._cpu_high = settings.AUTOSCALE_CPU_THRESHOLD_HIGH
        self._cpu_low = settings.AUTOSCALE_CPU_THRESHOLD_LOW
        self._memory_high = settings.AUTOSCALE_MEMORY_THRESHOLD_HIGH
        self._memory_low = settings.AUTOSCALE_MEMORY_THRESHOLD_LOW
        self._queue_threshold = settings.AUTOSCALE_QUEUE_THRESHOLD
        self._cooldown_period = settings.AUTOSCALE_COOLDOWN_PERIOD
        self._scale_up_increment = settings.AUTOSCALE_SCALE_UP_INCREMENT
        self._scale_down_increment = settings.AUTOSCALE_SCALE_DOWN_INCREMENT

    async def start(self) -> None:
        """Start the autoscaling service."""
        self._running = True
        self._scaler_task = asyncio.create_task(self._scaling_loop())
        logger.info(
            "AutoScaler started",
            enabled=self._enabled,
            min_workers=self._min_workers,
            max_workers=self._max_workers
        )

    async def stop(self) -> None:
        """Stop the autoscaling service."""
        self._running = False
        if self._scaler_task:
            self._scaler_task.cancel()
            try:
                await self._scaler_task
            except asyncio.CancelledError:
                pass
        logger.info("AutoScaler stopped")

    async def _scaling_loop(self) -> None:
        """Main scaling loop."""
        while self._running:
            try:
                if self._enabled:
                    decision = await self._evaluate_scaling()
                    await self._execute_scaling(decision)

                await asyncio.sleep(settings.AUTOSCALE_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in autoscaling loop", error=str(e))
                await asyncio.sleep(5)

    async def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current resource metrics."""
        try:
            resources = await self.ray_service.get_cluster_resources()

            if not resources:
                return {}

            total = resources.get("total", {})
            available = resources.get("available", {})

            # Calculate usage percentages
            cpu_total = total.get("cpus", 1)
            cpu_available = available.get("cpus", 0)
            cpu_usage = ((cpu_total - cpu_available) / cpu_total) * 100 if cpu_total > 0 else 0

            memory_total = total.get("memory_bytes", 1)
            memory_available = available.get("memory_bytes", 0)
            memory_usage = ((memory_total - memory_available) / memory_total) * 100 if memory_total > 0 else 0

            # Get task queue depth
            tasks = await self.ray_service.list_tasks()
            pending_tasks = len([t for t in tasks if t.get("status") == "pending"])
            running_tasks = len([t for t in tasks if t.get("status") == "running"])

            return {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory_usage,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "total_tasks": pending_tasks + running_tasks
            }
        except Exception as e:
            logger.error("Failed to get current metrics", error=str(e))
            return {}

    async def _evaluate_scaling(self) -> ScalingDecision:
        """Evaluate whether scaling is needed."""
        metrics = await self._get_current_metrics()

        if not metrics:
            return ScalingDecision(
                action=ScalingAction.NO_ACTION,
                reason="Unable to get metrics",
                current_workers=self._current_workers,
                target_workers=self._current_workers,
                metrics={}
            )

        # Check cooldown period
        if self._last_scale_action:
            elapsed = (datetime.utcnow() - self._last_scale_action).total_seconds()
            if elapsed < self._cooldown_period:
                return ScalingDecision(
                    action=ScalingAction.COOLDOWN,
                    reason=f"In cooldown period ({int(self._cooldown_period - elapsed)}s remaining)",
                    current_workers=self._current_workers,
                    target_workers=self._current_workers,
                    metrics=metrics
                )

        cpu_usage = metrics.get("cpu_usage_percent", 0)
        memory_usage = metrics.get("memory_usage_percent", 0)
        pending_tasks = metrics.get("pending_tasks", 0)

        # Check if we need to scale up
        scale_up_reasons = []
        if cpu_usage > self._cpu_high:
            scale_up_reasons.append(f"CPU usage {cpu_usage:.1f}% > {self._cpu_high}%")
        if memory_usage > self._memory_high:
            scale_up_reasons.append(f"Memory usage {memory_usage:.1f}% > {self._memory_high}%")
        if pending_tasks > self._queue_threshold:
            scale_up_reasons.append(f"Queue depth {pending_tasks} > {self._queue_threshold}")

        if scale_up_reasons and self._current_workers < self._max_workers:
            target = min(
                self._current_workers + self._scale_up_increment,
                self._max_workers
            )
            return ScalingDecision(
                action=ScalingAction.SCALE_UP,
                reason="; ".join(scale_up_reasons),
                current_workers=self._current_workers,
                target_workers=target,
                metrics=metrics
            )

        # Check if we need to scale down
        scale_down_reasons = []
        if cpu_usage < self._cpu_low:
            scale_down_reasons.append(f"CPU usage {cpu_usage:.1f}% < {self._cpu_low}%")
        if memory_usage < self._memory_low:
            scale_down_reasons.append(f"Memory usage {memory_usage:.1f}% < {self._memory_low}%")

        if scale_down_reasons and self._current_workers > self._min_workers:
            target = max(
                self._current_workers - self._scale_down_increment,
                self._min_workers
            )
            return ScalingDecision(
                action=ScalingAction.SCALE_DOWN,
                reason="; ".join(scale_down_reasons),
                current_workers=self._current_workers,
                target_workers=target,
                metrics=metrics
            )

        return ScalingDecision(
            action=ScalingAction.NO_ACTION,
            reason="Metrics within acceptable range",
            current_workers=self._current_workers,
            target_workers=self._current_workers,
            metrics=metrics
        )

    async def _execute_scaling(self, decision: ScalingDecision) -> None:
        """Execute a scaling decision."""
        if decision.action in [ScalingAction.NO_ACTION, ScalingAction.COOLDOWN]:
            return

        try:
            # Perform the scaling action
            if decision.action == ScalingAction.SCALE_UP:
                await self._scale_up(decision.target_workers - decision.current_workers)
            elif decision.action == ScalingAction.SCALE_DOWN:
                await self._scale_down(decision.current_workers - decision.target_workers)

            self._current_workers = decision.target_workers
            self._last_scale_action = datetime.utcnow()

            # Record the scaling event
            event = decision.to_dict()
            event["executed"] = True
            self._scaling_history.append(event)

            # Keep only last 100 events
            if len(self._scaling_history) > 100:
                self._scaling_history = self._scaling_history[-100:]

            logger.info(
                "Scaling action executed",
                action=decision.action.value,
                from_workers=decision.current_workers,
                to_workers=decision.target_workers,
                reason=decision.reason
            )

        except Exception as e:
            logger.error(
                "Failed to execute scaling action",
                action=decision.action.value,
                error=str(e)
            )

    async def _scale_up(self, count: int) -> None:
        """Scale up by adding workers."""
        # In a real implementation, this would request more workers from
        # Ray or Kubernetes. For now, we just log the action.
        logger.info("Scaling up", additional_workers=count)

        # Request additional resources from resource manager
        await self.resource_manager.request_workers(count)

    async def _scale_down(self, count: int) -> None:
        """Scale down by removing workers."""
        # In a real implementation, this would remove workers.
        logger.info("Scaling down", workers_to_remove=count)

        # Release resources through resource manager
        await self.resource_manager.release_workers(count)

    async def set_enabled(self, enabled: bool) -> None:
        """Enable or disable autoscaling."""
        self._enabled = enabled
        logger.info("AutoScaler enabled state changed", enabled=enabled)

    async def is_enabled(self) -> bool:
        """Check if autoscaling is enabled."""
        return self._enabled

    async def get_config(self) -> Dict[str, Any]:
        """Get current autoscaling configuration."""
        return {
            "enabled": self._enabled,
            "min_workers": self._min_workers,
            "max_workers": self._max_workers,
            "current_workers": self._current_workers,
            "cpu_threshold_high": self._cpu_high,
            "cpu_threshold_low": self._cpu_low,
            "memory_threshold_high": self._memory_high,
            "memory_threshold_low": self._memory_low,
            "queue_threshold": self._queue_threshold,
            "cooldown_period_seconds": self._cooldown_period,
            "scale_up_increment": self._scale_up_increment,
            "scale_down_increment": self._scale_down_increment,
            "check_interval_seconds": settings.AUTOSCALE_CHECK_INTERVAL
        }

    async def update_config(
        self,
        min_workers: Optional[int] = None,
        max_workers: Optional[int] = None,
        cpu_threshold_high: Optional[float] = None,
        cpu_threshold_low: Optional[float] = None,
        memory_threshold_high: Optional[float] = None,
        memory_threshold_low: Optional[float] = None,
        queue_threshold: Optional[int] = None,
        cooldown_period: Optional[int] = None,
        scale_up_increment: Optional[int] = None,
        scale_down_increment: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update autoscaling configuration."""
        if min_workers is not None:
            self._min_workers = min_workers
        if max_workers is not None:
            self._max_workers = max_workers
        if cpu_threshold_high is not None:
            self._cpu_high = cpu_threshold_high
        if cpu_threshold_low is not None:
            self._cpu_low = cpu_threshold_low
        if memory_threshold_high is not None:
            self._memory_high = memory_threshold_high
        if memory_threshold_low is not None:
            self._memory_low = memory_threshold_low
        if queue_threshold is not None:
            self._queue_threshold = queue_threshold
        if cooldown_period is not None:
            self._cooldown_period = cooldown_period
        if scale_up_increment is not None:
            self._scale_up_increment = scale_up_increment
        if scale_down_increment is not None:
            self._scale_down_increment = scale_down_increment

        logger.info("AutoScaler configuration updated")
        return await self.get_config()

    async def get_scaling_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scaling history."""
        return self._scaling_history[-limit:]

    async def get_current_state(self) -> Dict[str, Any]:
        """Get current autoscaler state."""
        metrics = await self._get_current_metrics()
        in_cooldown = False
        cooldown_remaining = 0

        if self._last_scale_action:
            elapsed = (datetime.utcnow() - self._last_scale_action).total_seconds()
            if elapsed < self._cooldown_period:
                in_cooldown = True
                cooldown_remaining = int(self._cooldown_period - elapsed)

        return {
            "enabled": self._enabled,
            "current_workers": self._current_workers,
            "in_cooldown": in_cooldown,
            "cooldown_remaining_seconds": cooldown_remaining,
            "last_scale_action": self._last_scale_action.isoformat() if self._last_scale_action else None,
            "current_metrics": metrics
        }

    async def trigger_manual_scale(self, target_workers: int) -> Dict[str, Any]:
        """Manually trigger scaling to a specific number of workers."""
        if target_workers < self._min_workers or target_workers > self._max_workers:
            raise ValueError(
                f"Target workers must be between {self._min_workers} and {self._max_workers}"
            )

        current = self._current_workers

        if target_workers > current:
            action = ScalingAction.SCALE_UP
            await self._scale_up(target_workers - current)
        elif target_workers < current:
            action = ScalingAction.SCALE_DOWN
            await self._scale_down(current - target_workers)
        else:
            action = ScalingAction.NO_ACTION

        self._current_workers = target_workers
        self._last_scale_action = datetime.utcnow()

        result = {
            "action": action.value,
            "previous_workers": current,
            "current_workers": target_workers,
            "timestamp": self._last_scale_action.isoformat()
        }

        # Record manual scaling event
        self._scaling_history.append({
            **result,
            "reason": "Manual scaling",
            "manual": True
        })

        logger.info(
            "Manual scaling executed",
            from_workers=current,
            to_workers=target_workers
        )

        return result
