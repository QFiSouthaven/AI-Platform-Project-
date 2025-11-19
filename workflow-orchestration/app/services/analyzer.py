"""
Requirement analysis service.

Analyzes user requirements and suggests workflow structures and task configurations.
"""

import logging
import re
from typing import Optional

from app.models.task import TaskType
from app.config import settings

logger = logging.getLogger(__name__)


class RequirementAnalyzer:
    """Service for analyzing requirements and generating workflow suggestions."""

    def __init__(self):
        """Initialize the requirement analyzer."""
        # Keywords for task type detection
        self._task_keywords = {
            TaskType.CODE_GENERATION: [
                "generate", "create code", "write code", "implement",
                "develop", "build", "code", "program", "script"
            ],
            TaskType.DATA_PROCESSING: [
                "process data", "transform data", "etl", "data pipeline",
                "clean data", "parse", "extract", "load data"
            ],
            TaskType.MODEL_INFERENCE: [
                "predict", "inference", "classify", "model",
                "ml", "machine learning", "ai model", "neural"
            ],
            TaskType.API_CALL: [
                "api", "http", "rest", "call endpoint", "request",
                "fetch", "external service", "integration"
            ],
            TaskType.NOTIFICATION: [
                "notify", "alert", "email", "send message",
                "notification", "slack", "webhook"
            ],
            TaskType.VALIDATION: [
                "validate", "verify", "check", "test",
                "assert", "ensure", "quality"
            ],
            TaskType.TRANSFORM: [
                "transform", "convert", "map", "format",
                "serialize", "deserialize"
            ],
            TaskType.AGGREGATION: [
                "aggregate", "combine", "merge", "join",
                "collect", "summarize", "reduce"
            ],
        }

    async def analyze_requirements(
        self,
        requirements: str,
        context: Optional[dict] = None
    ) -> dict:
        """
        Analyze requirements and generate workflow suggestions.

        Args:
            requirements: User requirements text
            context: Additional context for analysis

        Returns:
            Analysis results with workflow and task suggestions
        """
        logger.info(f"Analyzing requirements: {requirements[:100]}...")

        # Parse requirements into components
        components = self._parse_requirements(requirements)

        # Identify task types
        suggested_tasks = self._identify_tasks(components)

        # Build workflow structure
        workflow_structure = self._build_workflow_structure(suggested_tasks)

        # Estimate duration
        estimated_duration = self._estimate_duration(suggested_tasks)

        # Calculate confidence score
        confidence = self._calculate_confidence(requirements, suggested_tasks)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            requirements,
            suggested_tasks,
            context
        )

        return {
            "suggested_workflow": workflow_structure,
            "suggested_tasks": suggested_tasks,
            "estimated_duration": estimated_duration,
            "confidence_score": confidence,
            "recommendations": recommendations,
        }

    def _parse_requirements(self, requirements: str) -> list[str]:
        """
        Parse requirements into individual components.

        Args:
            requirements: Requirements text

        Returns:
            List of requirement components
        """
        # Split by common delimiters
        components = []

        # Split by numbered items (1., 2., etc.)
        numbered = re.split(r'\d+\.\s+', requirements)

        # Split by bullet points
        for item in numbered:
            bullets = re.split(r'[-*]\s+', item)
            components.extend(bullets)

        # Split by "and", "then", semicolons
        final_components = []
        for component in components:
            parts = re.split(r'\s+(?:and|then|;)\s+', component, flags=re.IGNORECASE)
            final_components.extend(parts)

        # Clean up and filter
        cleaned = []
        for component in final_components:
            component = component.strip()
            if component and len(component) > 5:  # Filter out very short fragments
                cleaned.append(component)

        return cleaned if cleaned else [requirements]

    def _identify_tasks(self, components: list[str]) -> list[dict]:
        """
        Identify task types for each component.

        Args:
            components: Requirement components

        Returns:
            List of task suggestions
        """
        tasks = []

        for i, component in enumerate(components):
            task_type = self._detect_task_type(component)

            task = {
                "name": self._generate_task_name(component, i),
                "description": component,
                "task_type": task_type.value,
                "config": self._generate_task_config(task_type, component),
                "depends_on": [i - 1] if i > 0 else [],
                "retry_policy": {
                    "max_retries": 3,
                    "retry_delay": 60,
                    "exponential_backoff": True,
                },
                "timeout_seconds": self._estimate_task_timeout(task_type),
                "priority": len(components) - i,  # Earlier tasks have higher priority
            }

            tasks.append(task)

        return tasks

    def _detect_task_type(self, component: str) -> TaskType:
        """
        Detect the task type based on component text.

        Args:
            component: Requirement component

        Returns:
            Detected task type
        """
        component_lower = component.lower()

        scores = {}
        for task_type, keywords in self._task_keywords.items():
            score = sum(1 for kw in keywords if kw in component_lower)
            if score > 0:
                scores[task_type] = score

        if scores:
            return max(scores, key=scores.get)

        return TaskType.CUSTOM

    def _generate_task_name(self, component: str, index: int) -> str:
        """
        Generate a task name from component.

        Args:
            component: Requirement component
            index: Task index

        Returns:
            Task name
        """
        # Extract first few words
        words = component.split()[:4]
        name = "_".join(words).lower()

        # Clean up
        name = re.sub(r'[^a-z0-9_]', '', name)

        return f"task_{index}_{name}" if name else f"task_{index}"

    def _generate_task_config(
        self,
        task_type: TaskType,
        component: str
    ) -> dict:
        """
        Generate task configuration based on type and component.

        Args:
            task_type: Task type
            component: Requirement component

        Returns:
            Task configuration
        """
        config = {"description": component}

        if task_type == TaskType.CODE_GENERATION:
            config["language"] = "python"
            config["prompt"] = component
        elif task_type == TaskType.API_CALL:
            # Try to extract URL if present
            url_match = re.search(r'https?://\S+', component)
            if url_match:
                config["url"] = url_match.group()
            config["method"] = "GET"
        elif task_type == TaskType.NOTIFICATION:
            config["channel"] = "email"
            config["message"] = component
        elif task_type == TaskType.MODEL_INFERENCE:
            config["model_type"] = "default"
        elif task_type == TaskType.VALIDATION:
            config["validation_type"] = "schema"

        return config

    def _estimate_task_timeout(self, task_type: TaskType) -> int:
        """
        Estimate timeout for a task type.

        Args:
            task_type: Task type

        Returns:
            Timeout in seconds
        """
        timeouts = {
            TaskType.CODE_GENERATION: 600,
            TaskType.DATA_PROCESSING: 300,
            TaskType.MODEL_INFERENCE: 300,
            TaskType.API_CALL: 120,
            TaskType.NOTIFICATION: 60,
            TaskType.VALIDATION: 60,
            TaskType.TRANSFORM: 120,
            TaskType.AGGREGATION: 180,
            TaskType.CONDITIONAL: 30,
            TaskType.CUSTOM: 300,
        }

        return timeouts.get(task_type, 300)

    def _build_workflow_structure(self, tasks: list[dict]) -> dict:
        """
        Build workflow structure from tasks.

        Args:
            tasks: List of task suggestions

        Returns:
            Workflow structure
        """
        return {
            "name": f"generated_workflow_{len(tasks)}_tasks",
            "description": "Auto-generated workflow from requirements analysis",
            "version": "1.0.0",
            "definition": {
                "type": "sequential",
                "tasks": [task["name"] for task in tasks],
            },
            "is_template": False,
            "timeout_seconds": sum(task["timeout_seconds"] for task in tasks) + 300,
            "tags": ["auto-generated", "requirements-based"],
        }

    def _estimate_duration(self, tasks: list[dict]) -> int:
        """
        Estimate total workflow duration.

        Args:
            tasks: List of task suggestions

        Returns:
            Estimated duration in seconds
        """
        # Sum of task timeouts with 20% buffer
        total = sum(task["timeout_seconds"] for task in tasks)
        return int(total * 1.2)

    def _calculate_confidence(
        self,
        requirements: str,
        tasks: list[dict]
    ) -> float:
        """
        Calculate confidence score for the analysis.

        Args:
            requirements: Original requirements
            tasks: Suggested tasks

        Returns:
            Confidence score (0-1)
        """
        if not tasks:
            return 0.0

        # Factors for confidence
        factors = []

        # Length factor - longer requirements provide more context
        length_score = min(len(requirements) / 200, 1.0)
        factors.append(length_score)

        # Task identification factor
        identified_types = sum(
            1 for task in tasks
            if task["task_type"] != TaskType.CUSTOM.value
        )
        type_score = identified_types / len(tasks) if tasks else 0
        factors.append(type_score)

        # Structure factor - presence of clear steps
        has_steps = bool(re.search(r'\d+\.|\*|-', requirements))
        factors.append(1.0 if has_steps else 0.5)

        # Calculate average
        confidence = sum(factors) / len(factors)

        return round(confidence, 2)

    def _generate_recommendations(
        self,
        requirements: str,
        tasks: list[dict],
        context: Optional[dict]
    ) -> list[str]:
        """
        Generate recommendations for the workflow.

        Args:
            requirements: Original requirements
            tasks: Suggested tasks
            context: Additional context

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for error handling
        if not any("error" in requirements.lower() or "fail" in requirements.lower()
                   for _ in [1]):
            recommendations.append(
                "Consider adding error handling tasks for robustness"
            )

        # Check for validation
        has_validation = any(
            task["task_type"] == TaskType.VALIDATION.value
            for task in tasks
        )
        if not has_validation:
            recommendations.append(
                "Adding validation tasks can improve data quality"
            )

        # Check for notifications
        has_notification = any(
            task["task_type"] == TaskType.NOTIFICATION.value
            for task in tasks
        )
        if not has_notification and len(tasks) > 3:
            recommendations.append(
                "Consider adding notifications for workflow completion status"
            )

        # Check task count
        if len(tasks) > 10:
            recommendations.append(
                "Consider breaking down into smaller sub-workflows for better management"
            )

        # Check for parallel execution opportunities
        if all(task["depends_on"] for task in tasks[1:]):
            recommendations.append(
                "Some tasks might be able to run in parallel to improve performance"
            )

        return recommendations

    async def suggest_improvements(
        self,
        workflow_id: int,
        execution_history: list[dict]
    ) -> list[str]:
        """
        Suggest improvements based on execution history.

        Args:
            workflow_id: Workflow ID
            execution_history: Past execution data

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        if not execution_history:
            return ["No execution history available for analysis"]

        # Analyze failure patterns
        failures = [e for e in execution_history if e.get("status") == "failed"]
        if len(failures) > len(execution_history) * 0.3:
            suggestions.append(
                f"High failure rate ({len(failures)}/{len(execution_history)}). "
                "Consider reviewing task configurations and retry policies."
            )

        # Analyze durations
        durations = [
            e.get("duration", 0)
            for e in execution_history
            if e.get("duration")
        ]
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)

            if max_duration > avg_duration * 2:
                suggestions.append(
                    f"Execution time varies significantly. "
                    f"Consider investigating slow runs (max: {max_duration}s, avg: {avg_duration:.0f}s)."
                )

        # Analyze retry counts
        retries = sum(e.get("total_retries", 0) for e in execution_history)
        if retries > len(execution_history) * 2:
            suggestions.append(
                "High retry rate detected. Consider increasing timeouts or reviewing task reliability."
            )

        return suggestions if suggestions else ["Workflow is performing well"]
