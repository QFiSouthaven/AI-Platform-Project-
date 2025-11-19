"""
Health Monitor Service - Worker and Cluster Health Monitoring

This service monitors the health of Ray workers, nodes, and services,
providing health status and triggering alerts when issues are detected.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth:
    """Health information for a component."""

    def __init__(self, component_id: str, component_type: str):
        self.component_id = component_id
        self.component_type = component_type
        self.status = HealthStatus.UNKNOWN
        self.last_check = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_error = None
        self.metrics: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_error": self.last_error,
            "metrics": self.metrics
        }


class HealthMonitor:
    """
    Service for monitoring health of cluster components.
    """

    def __init__(self, ray_service, resource_manager):
        self.ray_service = ray_service
        self.resource_manager = resource_manager
        self._running = False
        self._monitor_task = None
        self._start_time = None
        self._components: Dict[str, ComponentHealth] = {}
        self._health_history: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []

    async def start(self) -> None:
        """Start the health monitoring service."""
        self._running = True
        self._start_time = datetime.utcnow()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Health monitor started")

    async def stop(self) -> None:
        """Stop the health monitoring service."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")

    def get_uptime(self) -> float:
        """Get service uptime in seconds."""
        if self._start_time:
            return (datetime.utcnow() - self._start_time).total_seconds()
        return 0.0

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_all_components()
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in health monitor loop", error=str(e))
                await asyncio.sleep(5)

    async def _check_all_components(self) -> None:
        """Check health of all components."""
        # Check Ray cluster
        await self._check_ray_cluster()

        # Check nodes
        await self._check_nodes()

        # Store health snapshot
        snapshot = await self.get_cluster_health()
        snapshot["timestamp"] = datetime.utcnow().isoformat()
        self._health_history.append(snapshot)

        # Keep only last 1000 snapshots
        if len(self._health_history) > 1000:
            self._health_history = self._health_history[-1000:]

    async def _check_ray_cluster(self) -> None:
        """Check Ray cluster health."""
        component_id = "ray_cluster"

        if component_id not in self._components:
            self._components[component_id] = ComponentHealth(
                component_id=component_id,
                component_type="cluster"
            )

        component = self._components[component_id]
        component.last_check = datetime.utcnow()

        try:
            is_healthy = await self.ray_service.is_healthy()
            resources = await self.ray_service.get_cluster_resources()

            if is_healthy:
                component.status = HealthStatus.HEALTHY
                component.consecutive_successes += 1
                component.consecutive_failures = 0
                component.last_error = None
            else:
                component.status = HealthStatus.UNHEALTHY
                component.consecutive_failures += 1
                component.consecutive_successes = 0

            component.metrics = resources

            # Check for degraded state
            if resources:
                cpu_usage = 1 - (resources["available"]["cpus"] / max(resources["total"]["cpus"], 1))
                if cpu_usage > 0.9:
                    component.status = HealthStatus.DEGRADED

        except Exception as e:
            component.status = HealthStatus.UNHEALTHY
            component.consecutive_failures += 1
            component.consecutive_successes = 0
            component.last_error = str(e)
            logger.error("Ray cluster health check failed", error=str(e))

        # Trigger alert if needed
        if component.consecutive_failures >= settings.HEALTH_FAILURE_THRESHOLD:
            await self._trigger_alert(
                component_id=component_id,
                severity="critical",
                message=f"Ray cluster unhealthy: {component.last_error}"
            )

    async def _check_nodes(self) -> None:
        """Check health of individual nodes."""
        try:
            nodes = await self.ray_service.get_nodes()

            for node in nodes:
                node_id = node["node_id"]
                component_id = f"node_{node_id[:8]}"

                if component_id not in self._components:
                    self._components[component_id] = ComponentHealth(
                        component_id=component_id,
                        component_type="node"
                    )

                component = self._components[component_id]
                component.last_check = datetime.utcnow()

                if node["alive"]:
                    component.status = HealthStatus.HEALTHY
                    component.consecutive_successes += 1
                    component.consecutive_failures = 0
                    component.last_error = None
                else:
                    component.status = HealthStatus.UNHEALTHY
                    component.consecutive_failures += 1
                    component.consecutive_successes = 0
                    component.last_error = "Node not alive"

                    if component.consecutive_failures >= settings.HEALTH_FAILURE_THRESHOLD:
                        await self._trigger_alert(
                            component_id=component_id,
                            severity="warning",
                            message=f"Node {node_id[:8]} is unhealthy"
                        )

                component.metrics = node.get("resources", {})

        except Exception as e:
            logger.error("Node health check failed", error=str(e))

    async def _trigger_alert(
        self,
        component_id: str,
        severity: str,
        message: str
    ) -> None:
        """Trigger a health alert."""
        alert = {
            "component_id": component_id,
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False
        }

        self._alerts.append(alert)
        logger.warning(
            "Health alert triggered",
            component_id=component_id,
            severity=severity,
            message=message
        )

        # Keep only last 100 alerts
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]

    async def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health status."""
        if not self._components:
            return {"status": "unknown", "components": {}}

        statuses = [c.status for c in self._components.values()]

        # Determine overall status
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN

        return {
            "status": overall_status.value,
            "healthy_components": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
            "unhealthy_components": sum(1 for s in statuses if s == HealthStatus.UNHEALTHY),
            "degraded_components": sum(1 for s in statuses if s == HealthStatus.DEGRADED),
            "total_components": len(self._components)
        }

    async def get_component_health(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get health status of a specific component."""
        component = self._components.get(component_id)
        if component:
            return component.to_dict()
        return None

    async def get_all_components_health(self) -> List[Dict[str, Any]]:
        """Get health status of all components."""
        return [c.to_dict() for c in self._components.values()]

    async def get_health_history(
        self,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get health history snapshots."""
        history = self._health_history

        if since:
            history = [
                h for h in history
                if datetime.fromisoformat(h["timestamp"]) >= since
            ]

        return history[-limit:]

    async def get_alerts(
        self,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get health alerts with optional filters."""
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]

        if acknowledged is not None:
            alerts = [a for a in alerts if a["acknowledged"] == acknowledged]

        return alerts[-limit:]

    async def acknowledge_alert(self, alert_index: int) -> bool:
        """Acknowledge an alert by its index."""
        if 0 <= alert_index < len(self._alerts):
            self._alerts[alert_index]["acknowledged"] = True
            return True
        return False

    async def clear_alerts(self) -> int:
        """Clear all acknowledged alerts."""
        initial_count = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a["acknowledged"]]
        return initial_count - len(self._alerts)
