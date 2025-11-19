"""
Application assembly service for the Data Integration module.

Assembles application components and data from various sources.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class ApplicationAssembler:
    """
    Assembles application components and data pipelines.

    Coordinates data from multiple sources and assembles them
    into cohesive application structures.
    """

    def __init__(self, cache_manager, kafka_producer):
        """
        Initialize the application assembler.

        Args:
            cache_manager: CacheManager instance for caching operations
            kafka_producer: KafkaProducerManager for publishing events
        """
        self.cache_manager = cache_manager
        self.kafka_producer = kafka_producer
        self._assembly_stats = {
            "total_assemblies": 0,
            "successful": 0,
            "failed": 0,
        }

    async def assemble_workflow_context(
        self, workflow_id: str, include_tasks: bool = True
    ) -> Dict[str, Any]:
        """
        Assemble complete workflow context from cache.

        Args:
            workflow_id: ID of the workflow
            include_tasks: Whether to include task details

        Returns:
            Dict containing assembled workflow context
        """
        logger.info("Assembling workflow context", workflow_id=workflow_id)

        context = {
            "workflow_id": workflow_id,
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "workflow": None,
            "tasks": [],
            "metadata": {},
        }

        try:
            # Get workflow info from cache
            workflow_data = await self.cache_manager.get(f"workflow:{workflow_id}")
            if workflow_data:
                context["workflow"] = workflow_data

            # Get workflow progress
            progress = await self.cache_manager.get(f"workflow:{workflow_id}:progress")
            context["metadata"]["progress"] = progress or 0

            # Get tasks if requested
            if include_tasks:
                # Get task list for workflow
                task_list = await self.cache_manager.get(f"workflow:{workflow_id}:tasks")
                if task_list:
                    tasks = []
                    for task_id in task_list:
                        task_data = await self.cache_manager.get(f"task:{task_id}")
                        task_result = await self.cache_manager.get(f"task:{task_id}:result")
                        if task_data:
                            task_data["result"] = task_result
                            tasks.append(task_data)
                    context["tasks"] = tasks

            self._assembly_stats["total_assemblies"] += 1
            self._assembly_stats["successful"] += 1
            logger.info("Workflow context assembled", workflow_id=workflow_id)

        except Exception as e:
            logger.error(
                "Failed to assemble workflow context",
                workflow_id=workflow_id,
                error=str(e),
            )
            self._assembly_stats["failed"] += 1
            context["error"] = str(e)

        return context

    async def assemble_user_profile(
        self, user_id: str, include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Assemble complete user profile from cache.

        Args:
            user_id: ID of the user
            include_history: Whether to include activity history

        Returns:
            Dict containing assembled user profile
        """
        logger.info("Assembling user profile", user_id=user_id)

        profile = {
            "user_id": user_id,
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "user": None,
            "preferences": {},
            "history": [],
            "metadata": {},
        }

        try:
            # Get user data from cache
            user_data = await self.cache_manager.get(f"user:{user_id}")
            if user_data:
                profile["user"] = user_data

            # Get user preferences
            preferences = await self.cache_manager.get(f"user:{user_id}:preferences")
            if preferences:
                profile["preferences"] = preferences

            # Get activity history if requested
            if include_history:
                history = await self.cache_manager.get(f"user:{user_id}:history")
                if history:
                    profile["history"] = history

            # Get user stats
            stats = await self.cache_manager.get(f"user:{user_id}:stats")
            if stats:
                profile["metadata"]["stats"] = stats

            self._assembly_stats["total_assemblies"] += 1
            self._assembly_stats["successful"] += 1
            logger.info("User profile assembled", user_id=user_id)

        except Exception as e:
            logger.error(
                "Failed to assemble user profile",
                user_id=user_id,
                error=str(e),
            )
            self._assembly_stats["failed"] += 1
            profile["error"] = str(e)

        return profile

    async def assemble_model_registry(
        self, filter_loaded: bool = False
    ) -> Dict[str, Any]:
        """
        Assemble model registry information.

        Args:
            filter_loaded: Only include currently loaded models

        Returns:
            Dict containing model registry information
        """
        logger.info("Assembling model registry", filter_loaded=filter_loaded)

        registry = {
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "models": [],
            "loaded_models": [],
            "total_count": 0,
            "metadata": {},
        }

        try:
            # Get loaded models list
            loaded_models = await self.cache_manager.get("models:loaded") or []
            registry["loaded_models"] = loaded_models

            if filter_loaded:
                # Only get info for loaded models
                for model_id in loaded_models:
                    model_info = await self.cache_manager.get(f"model:{model_id}:info")
                    if model_info:
                        registry["models"].append(model_info)
            else:
                # Get all registered models
                all_models = await self.cache_manager.get("models:registry") or []
                for model_id in all_models:
                    model_info = await self.cache_manager.get(f"model:{model_id}:info")
                    if model_info:
                        model_info["is_loaded"] = model_id in loaded_models
                        registry["models"].append(model_info)

            registry["total_count"] = len(registry["models"])
            self._assembly_stats["total_assemblies"] += 1
            self._assembly_stats["successful"] += 1
            logger.info("Model registry assembled", count=registry["total_count"])

        except Exception as e:
            logger.error("Failed to assemble model registry", error=str(e))
            self._assembly_stats["failed"] += 1
            registry["error"] = str(e)

        return registry

    async def assemble_pipeline_data(
        self, pipeline_id: str, stages: List[str]
    ) -> Dict[str, Any]:
        """
        Assemble data for a processing pipeline.

        Args:
            pipeline_id: ID of the pipeline
            stages: List of stage names to assemble

        Returns:
            Dict containing assembled pipeline data
        """
        logger.info("Assembling pipeline data", pipeline_id=pipeline_id, stages=stages)

        pipeline_data = {
            "pipeline_id": pipeline_id,
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "stages": {},
            "metadata": {},
        }

        try:
            for stage in stages:
                # Get stage data from cache
                stage_key = f"pipeline:{pipeline_id}:stage:{stage}"
                stage_data = await self.cache_manager.get(stage_key)
                if stage_data:
                    pipeline_data["stages"][stage] = stage_data
                else:
                    pipeline_data["stages"][stage] = {"status": "not_found"}

            # Get pipeline metadata
            metadata_key = f"pipeline:{pipeline_id}:metadata"
            metadata = await self.cache_manager.get(metadata_key)
            if metadata:
                pipeline_data["metadata"] = metadata

            self._assembly_stats["total_assemblies"] += 1
            self._assembly_stats["successful"] += 1
            logger.info("Pipeline data assembled", pipeline_id=pipeline_id)

        except Exception as e:
            logger.error(
                "Failed to assemble pipeline data",
                pipeline_id=pipeline_id,
                error=str(e),
            )
            self._assembly_stats["failed"] += 1
            pipeline_data["error"] = str(e)

        return pipeline_data

    async def assemble_dashboard_data(
        self, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assemble data for dashboard display.

        Args:
            user_id: Optional user ID for personalized data

        Returns:
            Dict containing dashboard data
        """
        logger.info("Assembling dashboard data", user_id=user_id)

        dashboard = {
            "assembled_at": datetime.now(timezone.utc).isoformat(),
            "statistics": {},
            "recent_activity": [],
            "system_status": {},
        }

        try:
            # Get system statistics
            stats_keys = [
                "stats:user_count",
                "stats:workflow_count",
                "stats:task_count",
                "stats:model_count",
            ]

            for key in stats_keys:
                value = await self.cache_manager.get(key)
                stat_name = key.replace("stats:", "")
                dashboard["statistics"][stat_name] = value or 0

            # Get system status
            dashboard["system_status"] = {
                "cache": "operational",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Get user-specific data if user_id provided
            if user_id:
                user_profile = await self.assemble_user_profile(user_id)
                dashboard["user"] = user_profile.get("user", {})

                # Get recent user activity
                history = await self.cache_manager.get(f"user:{user_id}:history")
                if history:
                    dashboard["recent_activity"] = history[-10:]  # Last 10 activities

            self._assembly_stats["total_assemblies"] += 1
            self._assembly_stats["successful"] += 1
            logger.info("Dashboard data assembled")

        except Exception as e:
            logger.error("Failed to assemble dashboard data", error=str(e))
            self._assembly_stats["failed"] += 1
            dashboard["error"] = str(e)

        return dashboard

    async def invalidate_assembly_cache(
        self, entity_type: str, entity_id: str
    ) -> int:
        """
        Invalidate cached assembly data for an entity.

        Args:
            entity_type: Type of entity (workflow, user, model, pipeline)
            entity_id: ID of the entity

        Returns:
            Number of cache keys invalidated
        """
        logger.info(
            "Invalidating assembly cache",
            entity_type=entity_type,
            entity_id=entity_id,
        )

        patterns = {
            "workflow": [
                f"workflow:{entity_id}",
                f"workflow:{entity_id}:*",
            ],
            "user": [
                f"user:{entity_id}",
                f"user:{entity_id}:*",
            ],
            "model": [
                f"model:{entity_id}",
                f"model:{entity_id}:*",
            ],
            "pipeline": [
                f"pipeline:{entity_id}",
                f"pipeline:{entity_id}:*",
            ],
        }

        invalidated = 0
        for pattern in patterns.get(entity_type, []):
            count = await self.cache_manager.delete_pattern(pattern)
            invalidated += count

        logger.info(
            "Assembly cache invalidated",
            entity_type=entity_type,
            entity_id=entity_id,
            keys_invalidated=invalidated,
        )

        return invalidated

    def get_stats(self) -> Dict[str, Any]:
        """
        Get assembly statistics.

        Returns:
            Dict containing assembly stats
        """
        return {
            "total_assemblies": self._assembly_stats["total_assemblies"],
            "successful": self._assembly_stats["successful"],
            "failed": self._assembly_stats["failed"],
            "success_rate": (
                self._assembly_stats["successful"]
                / self._assembly_stats["total_assemblies"]
                * 100
                if self._assembly_stats["total_assemblies"] > 0
                else 0
            ),
        }
