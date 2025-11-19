"""
Task scheduler with dependency resolution and execution management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.task import TaskStatus
from app.models.workflow import ExecutionStatus
from app.utils.dag import DAGResolver

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler for managing task execution scheduling and dependency resolution."""

    def __init__(self):
        """Initialize the task scheduler."""
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._running_tasks: dict[int, asyncio.Task] = {}
        self._task_queues: dict[int, asyncio.Queue] = {}

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """Get or create the scheduler instance."""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(
                job_defaults={
                    'coalesce': settings.SCHEDULER_JOB_COALESCE,
                    'max_instances': settings.SCHEDULER_MAX_WORKERS,
                    'misfire_grace_time': settings.SCHEDULER_MISFIRE_GRACE_TIME,
                }
            )
        return self._scheduler

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Task scheduler shutdown")

    def schedule_workflow(
        self,
        workflow_id: int,
        execution_id: int,
        trigger_type: str = "immediate",
        trigger_config: Optional[dict] = None,
        callback=None
    ) -> str:
        """
        Schedule a workflow execution.

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID
            trigger_type: Type of trigger (immediate, cron, interval, date)
            trigger_config: Trigger configuration
            callback: Callback function to execute the workflow

        Returns:
            Job ID
        """
        job_id = f"workflow_{workflow_id}_exec_{execution_id}"
        trigger = self._create_trigger(trigger_type, trigger_config or {})

        self.scheduler.add_job(
            callback,
            trigger=trigger,
            id=job_id,
            args=[workflow_id, execution_id],
            replace_existing=True,
        )

        logger.info(
            f"Scheduled workflow execution",
            extra={
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "job_id": job_id,
                "trigger_type": trigger_type
            }
        )

        return job_id

    def _create_trigger(self, trigger_type: str, config: dict):
        """
        Create a trigger based on type and configuration.

        Args:
            trigger_type: Type of trigger
            config: Trigger configuration

        Returns:
            Trigger instance
        """
        if trigger_type == "immediate":
            return DateTrigger(run_date=datetime.utcnow())
        elif trigger_type == "cron":
            return CronTrigger(
                minute=config.get("minute", "*"),
                hour=config.get("hour", "*"),
                day=config.get("day", "*"),
                month=config.get("month", "*"),
                day_of_week=config.get("day_of_week", "*"),
            )
        elif trigger_type == "interval":
            return IntervalTrigger(
                seconds=config.get("seconds", 0),
                minutes=config.get("minutes", 0),
                hours=config.get("hours", 0),
            )
        elif trigger_type == "date":
            return DateTrigger(run_date=config.get("run_date"))
        else:
            raise ValueError(f"Unknown trigger type: {trigger_type}")

    def cancel_workflow(self, workflow_id: int, execution_id: int) -> bool:
        """
        Cancel a scheduled workflow execution.

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID

        Returns:
            True if cancelled, False if not found
        """
        job_id = f"workflow_{workflow_id}_exec_{execution_id}"

        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled workflow: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not cancel workflow {job_id}: {e}")
            return False

    async def get_executable_tasks(
        self,
        tasks: list,
        completed_task_ids: set[int]
    ) -> list:
        """
        Get tasks that are ready to execute based on dependency resolution.

        Args:
            tasks: List of tasks
            completed_task_ids: Set of completed task IDs

        Returns:
            List of tasks ready to execute
        """
        executable = []

        for task in tasks:
            if task.id in completed_task_ids:
                continue

            # Check if all dependencies are satisfied
            dependencies = task.depends_on or []
            if all(dep_id in completed_task_ids for dep_id in dependencies):
                executable.append(task)

        # Sort by priority (higher priority first)
        executable.sort(key=lambda t: t.priority, reverse=True)

        return executable

    async def resolve_task_order(self, tasks: list) -> list:
        """
        Resolve the execution order of tasks based on dependencies.

        Args:
            tasks: List of tasks

        Returns:
            Ordered list of tasks
        """
        resolver = DAGResolver()

        # Build dependency graph
        for task in tasks:
            resolver.add_node(task.id)
            for dep_id in (task.depends_on or []):
                resolver.add_edge(dep_id, task.id)

        # Get topological order
        order = resolver.topological_sort()

        # Map back to tasks
        task_map = {task.id: task for task in tasks}
        return [task_map[task_id] for task_id in order if task_id in task_map]

    async def check_task_timeout(
        self,
        task_execution,
        task
    ) -> bool:
        """
        Check if a task has exceeded its timeout.

        Args:
            task_execution: Task execution record
            task: Task definition

        Returns:
            True if timed out, False otherwise
        """
        if not task_execution.started_at:
            return False

        elapsed = (datetime.utcnow() - task_execution.started_at).total_seconds()
        return elapsed > task.timeout_seconds

    async def should_retry(
        self,
        task_execution,
        task
    ) -> bool:
        """
        Determine if a task should be retried.

        Args:
            task_execution: Task execution record
            task: Task definition

        Returns:
            True if should retry, False otherwise
        """
        retry_policy = task.retry_policy or {}
        max_retries = retry_policy.get("max_retries", settings.DEFAULT_RETRY_COUNT)

        if task_execution.retry_count >= max_retries:
            return False

        # Check if the error is retryable
        if task_execution.status == TaskStatus.TIMEOUT:
            return retry_policy.get("retry_on_timeout", True)

        return True

    def calculate_retry_delay(
        self,
        task,
        retry_count: int
    ) -> int:
        """
        Calculate the delay before retrying a task.

        Args:
            task: Task definition
            retry_count: Current retry count

        Returns:
            Delay in seconds
        """
        retry_policy = task.retry_policy or {}
        base_delay = retry_policy.get("retry_delay", settings.DEFAULT_RETRY_DELAY)

        if retry_policy.get("exponential_backoff", True):
            # Exponential backoff: delay * 2^retry_count
            return base_delay * (2 ** retry_count)

        return base_delay

    def get_scheduled_jobs(self) -> list[dict]:
        """
        Get list of scheduled jobs.

        Returns:
            List of job information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job.

        Args:
            job_id: Job ID

        Returns:
            True if paused, False if not found
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not pause job {job_id}: {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.

        Args:
            job_id: Job ID

        Returns:
            True if resumed, False if not found
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not resume job {job_id}: {e}")
            return False


# Global scheduler instance
task_scheduler = TaskScheduler()
