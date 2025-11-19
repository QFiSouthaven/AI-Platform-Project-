"""
Ray Service - Distributed Computing Management

This service manages the Ray cluster connection, task submission,
and distributed computing operations.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

import ray
import structlog
from ray.exceptions import RayTaskError, GetTimeoutError

from app.config import settings

logger = structlog.get_logger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskResult:
    """Container for task execution results."""

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: Optional[str] = None,
        execution_time: float = 0.0,
        retries: int = 0
    ):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.execution_time = execution_time
        self.retries = retries
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "retries": self.retries,
            "completed_at": self.completed_at.isoformat()
        }


class RayService:
    """
    Service for managing Ray cluster operations and distributed task execution.
    """

    def __init__(self):
        self._initialized = False
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._task_refs: Dict[str, ray.ObjectRef] = {}
        self._cluster_info: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """
        Initialize connection to Ray cluster.
        """
        try:
            # Configure Ray initialization options
            init_kwargs = {
                "address": settings.RAY_ADDRESS if settings.RAY_ADDRESS != "auto" else None,
                "namespace": settings.RAY_NAMESPACE,
                "log_to_driver": settings.RAY_LOG_TO_DRIVER,
                "include_dashboard": settings.RAY_INCLUDE_DASHBOARD,
                "dashboard_host": settings.RAY_DASHBOARD_HOST,
                "dashboard_port": settings.RAY_DASHBOARD_PORT,
                "_temp_dir": settings.RAY_TEMP_DIR,
            }

            # Add resource limits if specified
            if settings.RAY_NUM_CPUS:
                init_kwargs["num_cpus"] = settings.RAY_NUM_CPUS
            if settings.RAY_NUM_GPUS:
                init_kwargs["num_gpus"] = settings.RAY_NUM_GPUS
            if settings.RAY_OBJECT_STORE_MEMORY:
                init_kwargs["object_store_memory"] = settings.RAY_OBJECT_STORE_MEMORY

            # Filter out None values
            init_kwargs = {k: v for k, v in init_kwargs.items() if v is not None}

            # Initialize Ray
            if not ray.is_initialized():
                ray.init(**init_kwargs)

            self._initialized = True
            self._cluster_info = await self._get_cluster_info()

            logger.info(
                "Ray cluster initialized",
                cluster_info=self._cluster_info
            )

        except Exception as e:
            logger.error("Failed to initialize Ray cluster", error=str(e))
            raise

    async def shutdown(self) -> None:
        """
        Shutdown Ray connection and cleanup resources.
        """
        try:
            # Cancel all pending tasks
            for task_id in list(self._task_refs.keys()):
                await self.cancel_task(task_id)

            if ray.is_initialized():
                ray.shutdown()

            self._initialized = False
            logger.info("Ray cluster shutdown completed")

        except Exception as e:
            logger.error("Error during Ray shutdown", error=str(e))

    async def is_healthy(self) -> bool:
        """Check if Ray cluster is healthy and connected."""
        try:
            if not self._initialized or not ray.is_initialized():
                return False

            # Try to get cluster resources as a health check
            resources = ray.cluster_resources()
            return len(resources) > 0

        except Exception:
            return False

    async def is_ready(self) -> bool:
        """Check if service is ready to accept tasks."""
        return await self.is_healthy()

    async def _get_cluster_info(self) -> Dict[str, Any]:
        """Get current cluster information."""
        try:
            nodes = ray.nodes()
            resources = ray.cluster_resources()
            available = ray.available_resources()

            return {
                "num_nodes": len([n for n in nodes if n["Alive"]]),
                "total_cpus": resources.get("CPU", 0),
                "total_gpus": resources.get("GPU", 0),
                "total_memory": resources.get("memory", 0),
                "available_cpus": available.get("CPU", 0),
                "available_gpus": available.get("GPU", 0),
                "available_memory": available.get("memory", 0)
            }
        except Exception as e:
            logger.error("Failed to get cluster info", error=str(e))
            return {}

    async def submit_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        num_cpus: float = None,
        num_gpus: float = None,
        memory: int = None,
        timeout: int = None,
        max_retries: int = None
    ) -> str:
        """
        Submit a task for distributed execution.

        Args:
            task_id: Unique task identifier
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            num_cpus: Number of CPUs to reserve
            num_gpus: Number of GPUs to reserve
            memory: Memory in bytes to reserve
            timeout: Task timeout in seconds
            max_retries: Maximum retry attempts

        Returns:
            task_id: The submitted task ID
        """
        if not self._initialized:
            raise RuntimeError("Ray service not initialized")

        kwargs = kwargs or {}
        timeout = timeout or settings.TASK_DEFAULT_TIMEOUT
        max_retries = max_retries or settings.TASK_MAX_RETRIES

        # Create remote function with resource requirements
        remote_options = {}
        if num_cpus is not None:
            remote_options["num_cpus"] = num_cpus
        if num_gpus is not None:
            remote_options["num_gpus"] = num_gpus
        if memory is not None:
            remote_options["memory"] = memory
        if max_retries > 0:
            remote_options["max_retries"] = max_retries
            remote_options["retry_exceptions"] = True

        # Create remote function
        if remote_options:
            remote_func = ray.remote(**remote_options)(func)
        else:
            remote_func = ray.remote(func)

        # Submit task
        try:
            ref = remote_func.remote(*args, **kwargs)
            self._task_refs[task_id] = ref

            # Store task metadata
            self._tasks[task_id] = {
                "task_id": task_id,
                "status": TaskStatus.RUNNING,
                "submitted_at": datetime.utcnow().isoformat(),
                "timeout": timeout,
                "max_retries": max_retries,
                "retries": 0
            }

            logger.info(
                "Task submitted",
                task_id=task_id,
                timeout=timeout,
                resources=remote_options
            )

            return task_id

        except Exception as e:
            logger.error("Failed to submit task", task_id=task_id, error=str(e))
            raise

    async def get_task_result(
        self,
        task_id: str,
        timeout: Optional[int] = None
    ) -> TaskResult:
        """
        Get the result of a submitted task.

        Args:
            task_id: Task identifier
            timeout: Timeout in seconds to wait for result

        Returns:
            TaskResult with status and result/error
        """
        if task_id not in self._task_refs:
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error="Task not found"
            )

        ref = self._task_refs[task_id]
        task_meta = self._tasks.get(task_id, {})
        timeout = timeout or task_meta.get("timeout", settings.TASK_DEFAULT_TIMEOUT)

        start_time = time.time()

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ray.get(ref, timeout=timeout)
            )

            execution_time = time.time() - start_time

            # Update task status
            self._tasks[task_id]["status"] = TaskStatus.COMPLETED
            self._tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

            return TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                retries=task_meta.get("retries", 0)
            )

        except GetTimeoutError:
            self._tasks[task_id]["status"] = TaskStatus.TIMEOUT
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {timeout} seconds",
                execution_time=time.time() - start_time
            )

        except RayTaskError as e:
            self._tasks[task_id]["status"] = TaskStatus.FAILED
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time,
                retries=task_meta.get("retries", 0)
            )

        except Exception as e:
            self._tasks[task_id]["status"] = TaskStatus.FAILED
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the current status of a task.
        """
        if task_id not in self._tasks:
            return {"task_id": task_id, "status": "not_found"}

        task_meta = self._tasks[task_id]

        # Check if task is still running
        if task_meta["status"] == TaskStatus.RUNNING:
            ref = self._task_refs.get(task_id)
            if ref:
                ready, _ = ray.wait([ref], timeout=0)
                if ready:
                    # Task completed, get result
                    result = await self.get_task_result(task_id, timeout=1)
                    return {
                        "task_id": task_id,
                        "status": result.status.value,
                        "completed_at": result.completed_at.isoformat()
                    }

        return {
            "task_id": task_id,
            "status": task_meta["status"].value if isinstance(task_meta["status"], TaskStatus) else task_meta["status"],
            "submitted_at": task_meta.get("submitted_at"),
            "completed_at": task_meta.get("completed_at")
        }

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        """
        if task_id not in self._task_refs:
            return False

        try:
            ref = self._task_refs[task_id]
            ray.cancel(ref)

            self._tasks[task_id]["status"] = TaskStatus.CANCELLED
            self._tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

            # Cleanup
            del self._task_refs[task_id]

            logger.info("Task cancelled", task_id=task_id)
            return True

        except Exception as e:
            logger.error("Failed to cancel task", task_id=task_id, error=str(e))
            return False

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all tasks with optional status filter.
        """
        tasks = []
        for task_id, task_meta in self._tasks.items():
            task_status = task_meta.get("status")
            if status is None or task_status == status:
                tasks.append({
                    "task_id": task_id,
                    "status": task_status.value if isinstance(task_status, TaskStatus) else task_status,
                    "submitted_at": task_meta.get("submitted_at"),
                    "completed_at": task_meta.get("completed_at")
                })

        return tasks[:limit]

    async def get_cluster_resources(self) -> Dict[str, Any]:
        """
        Get current cluster resource usage and availability.
        """
        try:
            total = ray.cluster_resources()
            available = ray.available_resources()

            return {
                "total": {
                    "cpus": total.get("CPU", 0),
                    "gpus": total.get("GPU", 0),
                    "memory_bytes": total.get("memory", 0)
                },
                "available": {
                    "cpus": available.get("CPU", 0),
                    "gpus": available.get("GPU", 0),
                    "memory_bytes": available.get("memory", 0)
                },
                "used": {
                    "cpus": total.get("CPU", 0) - available.get("CPU", 0),
                    "gpus": total.get("GPU", 0) - available.get("GPU", 0),
                    "memory_bytes": total.get("memory", 0) - available.get("memory", 0)
                }
            }
        except Exception as e:
            logger.error("Failed to get cluster resources", error=str(e))
            return {}

    async def get_nodes(self) -> List[Dict[str, Any]]:
        """
        Get information about all nodes in the cluster.
        """
        try:
            nodes = ray.nodes()
            return [
                {
                    "node_id": node["NodeID"],
                    "alive": node["Alive"],
                    "node_manager_address": node["NodeManagerAddress"],
                    "resources": node["Resources"],
                    "labels": node.get("Labels", {})
                }
                for node in nodes
            ]
        except Exception as e:
            logger.error("Failed to get nodes", error=str(e))
            return []

    async def cleanup_completed_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up completed task references older than max_age.
        """
        cutoff = datetime.utcnow().timestamp() - max_age_seconds
        removed = 0

        for task_id in list(self._tasks.keys()):
            task_meta = self._tasks[task_id]
            if task_meta["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                completed_at = task_meta.get("completed_at")
                if completed_at:
                    completed_ts = datetime.fromisoformat(completed_at).timestamp()
                    if completed_ts < cutoff:
                        del self._tasks[task_id]
                        if task_id in self._task_refs:
                            del self._task_refs[task_id]
                        removed += 1

        if removed > 0:
            logger.info("Cleaned up completed tasks", count=removed)

        return removed
