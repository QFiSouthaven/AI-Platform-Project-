"""
Resource Manager Service - Resource Allocation and Management

This service manages resource allocation, reservations, and tracking
for the distributed computing infrastructure.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class ResourceType(str, Enum):
    """Types of resources that can be managed."""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    WORKER = "worker"


class ResourceReservation:
    """Represents a resource reservation."""

    def __init__(
        self,
        reservation_id: str,
        resource_type: ResourceType,
        amount: float,
        requester_id: str,
        expires_at: datetime
    ):
        self.reservation_id = reservation_id
        self.resource_type = resource_type
        self.amount = amount
        self.requester_id = requester_id
        self.created_at = datetime.utcnow()
        self.expires_at = expires_at
        self.released = False

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "resource_type": self.resource_type.value,
            "amount": self.amount,
            "requester_id": self.requester_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "released": self.released,
            "expired": self.is_expired()
        }


class ResourceManager:
    """
    Service for managing resource allocation and reservations.
    """

    def __init__(self):
        self._initialized = False
        self._reservations: Dict[str, ResourceReservation] = {}
        self._resource_limits: Dict[ResourceType, float] = {}
        self._resource_usage: Dict[ResourceType, float] = {}
        self._cleanup_task = None
        self._lock = asyncio.Lock()

        # Worker tracking
        self._workers: Dict[str, Dict[str, Any]] = {}
        self._worker_counter = 0

    async def initialize(self) -> None:
        """Initialize the resource manager."""
        # Set default resource limits
        self._resource_limits = {
            ResourceType.CPU: settings.MAX_WORKERS * settings.WORKERS_PER_NODE,
            ResourceType.GPU: settings.RAY_NUM_GPUS or 0,
            ResourceType.MEMORY: settings.MAX_WORKERS * settings.WORKER_MEMORY_MB * 1024 * 1024,
            ResourceType.WORKER: settings.MAX_WORKERS
        }

        # Initialize usage tracking
        self._resource_usage = {
            ResourceType.CPU: 0,
            ResourceType.GPU: 0,
            ResourceType.MEMORY: 0,
            ResourceType.WORKER: settings.MIN_WORKERS
        }

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self._initialized = True
        logger.info("Resource manager initialized", limits=self._resource_limits)

    async def cleanup(self) -> None:
        """Cleanup resources and stop background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self._initialized = False
        logger.info("Resource manager cleanup completed")

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired reservations."""
        while True:
            try:
                await self._cleanup_expired_reservations()
                await asyncio.sleep(settings.RESOURCE_CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))
                await asyncio.sleep(60)

    async def _cleanup_expired_reservations(self) -> None:
        """Remove expired reservations and release resources."""
        async with self._lock:
            expired = [
                res_id for res_id, res in self._reservations.items()
                if res.is_expired() and not res.released
            ]

            for res_id in expired:
                reservation = self._reservations[res_id]
                self._resource_usage[reservation.resource_type] -= reservation.amount
                reservation.released = True
                logger.info(
                    "Expired reservation released",
                    reservation_id=res_id,
                    resource_type=reservation.resource_type.value
                )

    async def reserve_resources(
        self,
        resource_type: ResourceType,
        amount: float,
        requester_id: str,
        timeout: int = None
    ) -> Optional[str]:
        """
        Reserve resources for a requester.

        Args:
            resource_type: Type of resource to reserve
            amount: Amount to reserve
            requester_id: ID of the requester
            timeout: Reservation timeout in seconds

        Returns:
            reservation_id if successful, None otherwise
        """
        timeout = timeout or settings.RESOURCE_RESERVATION_TIMEOUT

        async with self._lock:
            # Check availability
            limit = self._resource_limits.get(resource_type, 0)
            used = self._resource_usage.get(resource_type, 0)
            available = limit - used

            if amount > available:
                logger.warning(
                    "Insufficient resources for reservation",
                    resource_type=resource_type.value,
                    requested=amount,
                    available=available
                )
                return None

            # Create reservation
            reservation_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(seconds=timeout)

            reservation = ResourceReservation(
                reservation_id=reservation_id,
                resource_type=resource_type,
                amount=amount,
                requester_id=requester_id,
                expires_at=expires_at
            )

            self._reservations[reservation_id] = reservation
            self._resource_usage[resource_type] += amount

            logger.info(
                "Resources reserved",
                reservation_id=reservation_id,
                resource_type=resource_type.value,
                amount=amount,
                requester_id=requester_id
            )

            return reservation_id

    async def release_reservation(self, reservation_id: str) -> bool:
        """
        Release a resource reservation.

        Args:
            reservation_id: ID of the reservation to release

        Returns:
            True if released successfully, False otherwise
        """
        async with self._lock:
            if reservation_id not in self._reservations:
                return False

            reservation = self._reservations[reservation_id]

            if reservation.released:
                return False

            self._resource_usage[reservation.resource_type] -= reservation.amount
            reservation.released = True

            logger.info(
                "Reservation released",
                reservation_id=reservation_id,
                resource_type=reservation.resource_type.value,
                amount=reservation.amount
            )

            return True

    async def get_reservation(self, reservation_id: str) -> Optional[Dict[str, Any]]:
        """Get reservation details."""
        reservation = self._reservations.get(reservation_id)
        if reservation:
            return reservation.to_dict()
        return None

    async def get_resource_availability(self) -> Dict[str, Any]:
        """Get current resource availability."""
        availability = {}

        for resource_type in ResourceType:
            limit = self._resource_limits.get(resource_type, 0)
            used = self._resource_usage.get(resource_type, 0)

            availability[resource_type.value] = {
                "limit": limit,
                "used": used,
                "available": limit - used,
                "utilization_percent": (used / limit * 100) if limit > 0 else 0
            }

        return availability

    async def update_resource_limits(
        self,
        resource_type: ResourceType,
        limit: float
    ) -> None:
        """Update resource limits."""
        async with self._lock:
            self._resource_limits[resource_type] = limit
            logger.info(
                "Resource limit updated",
                resource_type=resource_type.value,
                new_limit=limit
            )

    async def request_workers(self, count: int) -> List[str]:
        """
        Request additional workers.

        Args:
            count: Number of workers to add

        Returns:
            List of worker IDs
        """
        async with self._lock:
            worker_ids = []

            for _ in range(count):
                worker_id = f"worker-{self._worker_counter:04d}"
                self._worker_counter += 1

                self._workers[worker_id] = {
                    "worker_id": worker_id,
                    "status": "starting",
                    "created_at": datetime.utcnow().isoformat(),
                    "cpu_allocated": settings.WORKER_CPU_FRACTION,
                    "memory_allocated_mb": settings.WORKER_MEMORY_MB
                }

                worker_ids.append(worker_id)

            self._resource_usage[ResourceType.WORKER] += count

            logger.info("Workers requested", count=count, worker_ids=worker_ids)

            return worker_ids

    async def release_workers(self, count: int) -> List[str]:
        """
        Release workers.

        Args:
            count: Number of workers to release

        Returns:
            List of released worker IDs
        """
        async with self._lock:
            # Get idle workers to release
            idle_workers = [
                wid for wid, w in self._workers.items()
                if w.get("status") == "idle"
            ]

            # If not enough idle workers, get any workers
            if len(idle_workers) < count:
                all_workers = list(self._workers.keys())
                idle_workers = all_workers[:count]

            workers_to_release = idle_workers[:count]

            for worker_id in workers_to_release:
                if worker_id in self._workers:
                    del self._workers[worker_id]

            self._resource_usage[ResourceType.WORKER] = max(
                0,
                self._resource_usage[ResourceType.WORKER] - len(workers_to_release)
            )

            logger.info("Workers released", count=len(workers_to_release), worker_ids=workers_to_release)

            return workers_to_release

    async def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get worker information."""
        return self._workers.get(worker_id)

    async def get_all_workers(self) -> List[Dict[str, Any]]:
        """Get information about all workers."""
        return list(self._workers.values())

    async def update_worker_status(
        self,
        worker_id: str,
        status: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update worker status and metrics.

        Args:
            worker_id: Worker identifier
            status: New status (starting, running, idle, stopping, stopped)
            metrics: Optional metrics to update

        Returns:
            True if updated successfully
        """
        async with self._lock:
            if worker_id not in self._workers:
                return False

            self._workers[worker_id]["status"] = status
            self._workers[worker_id]["last_updated"] = datetime.utcnow().isoformat()

            if metrics:
                self._workers[worker_id]["metrics"] = metrics

            return True

    async def get_active_reservations(
        self,
        requester_id: Optional[str] = None,
        resource_type: Optional[ResourceType] = None
    ) -> List[Dict[str, Any]]:
        """Get active (non-released, non-expired) reservations."""
        reservations = []

        for res in self._reservations.values():
            if res.released or res.is_expired():
                continue

            if requester_id and res.requester_id != requester_id:
                continue

            if resource_type and res.resource_type != resource_type:
                continue

            reservations.append(res.to_dict())

        return reservations

    async def get_resource_stats(self) -> Dict[str, Any]:
        """Get overall resource statistics."""
        availability = await self.get_resource_availability()
        active_reservations = len([
            r for r in self._reservations.values()
            if not r.released and not r.is_expired()
        ])

        return {
            "availability": availability,
            "total_reservations": len(self._reservations),
            "active_reservations": active_reservations,
            "total_workers": len(self._workers),
            "workers_by_status": self._count_workers_by_status()
        }

    def _count_workers_by_status(self) -> Dict[str, int]:
        """Count workers by their status."""
        counts = {}
        for worker in self._workers.values():
            status = worker.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
        return counts


# Import timedelta for reservation expiration
from datetime import timedelta
