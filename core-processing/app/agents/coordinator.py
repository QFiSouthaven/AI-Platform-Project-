"""
Multi-agent coordinator for orchestrating code processing tasks.

Manages multiple specialized agents and coordinates their work.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from app.agents.code_agent import AgentMessage, AgentState, CodeAgent
from app.agents.debug_agent import DebugAgent
from app.models.llm_models import ProgrammingLanguage
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class TaskType(str, Enum):
    """Types of coordinated tasks."""
    GENERATE = "generate"
    DEBUG = "debug"
    GENERATE_AND_DEBUG = "generate_and_debug"
    FULL_PIPELINE = "full_pipeline"


class WorkflowStep:
    """A step in a coordinated workflow."""

    def __init__(
        self,
        step_id: str,
        agent_type: str,
        task: str,
        dependencies: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.step_id = step_id
        self.agent_type = agent_type
        self.task = task
        self.dependencies = dependencies or []
        self.config = config or {}
        self.status = "pending"
        self.result = None
        self.error = None


class AgentCoordinator:
    """
    Coordinator for multi-agent code processing.

    Features:
    - Agent lifecycle management
    - Task routing and orchestration
    - Workflow execution
    - Result aggregation
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.coordinator_id = f"coordinator_{uuid.uuid4().hex[:8]}"
        self.agents: Dict[str, Any] = {}
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False

        # Initialize default agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize the default set of agents."""
        self.agents["code"] = CodeAgent(self.llm_service)
        self.agents["debug"] = DebugAgent(self.llm_service)

        logger.info(
            "Agents initialized",
            coordinator_id=self.coordinator_id,
            agents=list(self.agents.keys())
        )

    async def execute_task(
        self,
        task_type: TaskType,
        task_input: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a coordinated task.

        Args:
            task_type: Type of task to execute
            task_input: Input parameters for the task
            correlation_id: Request correlation ID

        Returns:
            Task execution result
        """
        execution_id = correlation_id or str(uuid.uuid4())

        logger.info(
            "Coordinator executing task",
            coordinator_id=self.coordinator_id,
            task_type=task_type,
            execution_id=execution_id
        )

        try:
            if task_type == TaskType.GENERATE:
                return await self._execute_generation(task_input, execution_id)

            elif task_type == TaskType.DEBUG:
                return await self._execute_debugging(task_input, execution_id)

            elif task_type == TaskType.GENERATE_AND_DEBUG:
                return await self._execute_generate_and_debug(task_input, execution_id)

            elif task_type == TaskType.FULL_PIPELINE:
                return await self._execute_full_pipeline(task_input, execution_id)

            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            logger.error(
                "Task execution failed",
                coordinator_id=self.coordinator_id,
                task_type=task_type,
                error=str(e),
                execution_id=execution_id
            )
            raise

    async def _execute_generation(
        self,
        task_input: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute code generation task."""
        code_agent = self.agents["code"]

        result = await code_agent.execute(
            task=task_input.get("task", ""),
            language=task_input.get("language", ProgrammingLanguage.PYTHON),
            context=task_input.get("context"),
            requirements=task_input.get("requirements"),
            correlation_id=execution_id
        )

        return {
            "execution_id": execution_id,
            "task_type": TaskType.GENERATE,
            "code": result["code"],
            "language": result["language"],
            "iterations": result["iterations"],
            "agent_id": result["agent_id"],
            "status": "completed"
        }

    async def _execute_debugging(
        self,
        task_input: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute debugging task."""
        debug_agent = self.agents["debug"]

        result = await debug_agent.execute(
            code=task_input.get("code", ""),
            language=task_input.get("language", ProgrammingLanguage.PYTHON),
            error_message=task_input.get("error_message"),
            stack_trace=task_input.get("stack_trace"),
            correlation_id=execution_id
        )

        return {
            "execution_id": execution_id,
            "task_type": TaskType.DEBUG,
            "fixed_code": result["fixed_code"],
            "bugs_found": result["bugs_found"],
            "analysis": result["analysis"],
            "agent_id": result["agent_id"],
            "status": "completed"
        }

    async def _execute_generate_and_debug(
        self,
        task_input: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute generation followed by debugging."""
        # Step 1: Generate code
        gen_result = await self._execute_generation(task_input, execution_id)

        # Step 2: Debug the generated code
        debug_input = {
            "code": gen_result["code"],
            "language": task_input.get("language", ProgrammingLanguage.PYTHON)
        }
        debug_result = await self._execute_debugging(debug_input, execution_id)

        return {
            "execution_id": execution_id,
            "task_type": TaskType.GENERATE_AND_DEBUG,
            "generated_code": gen_result["code"],
            "final_code": debug_result["fixed_code"],
            "bugs_found": debug_result["bugs_found"],
            "language": task_input.get("language", ProgrammingLanguage.PYTHON),
            "status": "completed"
        }

    async def _execute_full_pipeline(
        self,
        task_input: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute full pipeline: generate, debug, and optimize."""
        results = {
            "execution_id": execution_id,
            "task_type": TaskType.FULL_PIPELINE,
            "steps": [],
            "status": "completed"
        }

        # Step 1: Generate
        gen_result = await self._execute_generation(task_input, execution_id)
        results["steps"].append({
            "step": "generation",
            "result": gen_result
        })

        # Step 2: Debug
        debug_input = {
            "code": gen_result["code"],
            "language": task_input.get("language", ProgrammingLanguage.PYTHON)
        }
        debug_result = await self._execute_debugging(debug_input, execution_id)
        results["steps"].append({
            "step": "debugging",
            "result": debug_result
        })

        results["final_code"] = debug_result["fixed_code"]
        results["total_bugs_fixed"] = len(debug_result["bugs_found"])

        return results

    async def execute_workflow(
        self,
        workflow_id: str,
        steps: List[Dict[str, Any]],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a custom workflow with multiple steps.

        Args:
            workflow_id: Unique workflow identifier
            steps: List of workflow step definitions
            correlation_id: Request correlation ID

        Returns:
            Workflow execution results
        """
        execution_id = correlation_id or str(uuid.uuid4())

        # Convert to WorkflowStep objects
        workflow_steps = []
        for step_def in steps:
            step = WorkflowStep(
                step_id=step_def.get("step_id", str(uuid.uuid4())),
                agent_type=step_def.get("agent_type", "code"),
                task=step_def.get("task", ""),
                dependencies=step_def.get("dependencies", []),
                config=step_def.get("config", {})
            )
            workflow_steps.append(step)

        self.workflows[workflow_id] = workflow_steps

        logger.info(
            "Executing workflow",
            coordinator_id=self.coordinator_id,
            workflow_id=workflow_id,
            num_steps=len(workflow_steps),
            execution_id=execution_id
        )

        # Execute steps respecting dependencies
        completed_steps = set()
        results = {}

        while len(completed_steps) < len(workflow_steps):
            # Find steps that can be executed
            executable = []
            for step in workflow_steps:
                if step.step_id not in completed_steps:
                    if all(dep in completed_steps for dep in step.dependencies):
                        executable.append(step)

            if not executable:
                # Deadlock - dependencies cannot be satisfied
                raise RuntimeError(f"Workflow deadlock in {workflow_id}")

            # Execute all executable steps in parallel
            tasks = []
            for step in executable:
                task = self._execute_workflow_step(step, results)
                tasks.append(task)

            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for step, result in zip(executable, step_results):
                if isinstance(result, Exception):
                    step.status = "failed"
                    step.error = str(result)
                    logger.error(
                        "Workflow step failed",
                        workflow_id=workflow_id,
                        step_id=step.step_id,
                        error=str(result)
                    )
                else:
                    step.status = "completed"
                    step.result = result
                    results[step.step_id] = result

                completed_steps.add(step.step_id)

        return {
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "steps": [
                {
                    "step_id": s.step_id,
                    "status": s.status,
                    "result": s.result,
                    "error": s.error
                }
                for s in workflow_steps
            ],
            "status": "completed" if all(s.status == "completed" for s in workflow_steps) else "partial"
        }

    async def _execute_workflow_step(
        self,
        step: WorkflowStep,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        agent = self.agents.get(step.agent_type)
        if not agent:
            raise ValueError(f"Unknown agent type: {step.agent_type}")

        # Resolve task with previous results
        task = step.task
        for step_id, result in previous_results.items():
            if isinstance(result, dict) and "code" in result:
                task = task.replace(f"{{{{result.{step_id}.code}}}}", result["code"])

        # Execute based on agent type
        config = step.config
        if step.agent_type == "code":
            return await agent.execute(
                task=task,
                language=config.get("language", ProgrammingLanguage.PYTHON),
                context=config.get("context"),
                requirements=config.get("requirements")
            )
        elif step.agent_type == "debug":
            return await agent.execute(
                code=config.get("code", task),
                language=config.get("language", ProgrammingLanguage.PYTHON),
                error_message=config.get("error_message")
            )

        return {}

    def get_agent_status(self) -> Dict[str, str]:
        """Get status of all agents."""
        return {
            agent_id: str(agent.get_state())
            for agent_id, agent in self.agents.items()
        }

    async def send_message(self, message: AgentMessage):
        """
        Send a message to an agent.

        Args:
            message: Message to send
        """
        agent = self.agents.get(message.receiver.split("_")[0])
        if agent:
            response = await agent.receive_message(message)
            if response:
                await self.message_queue.put(response)

    async def broadcast_message(
        self,
        content: str,
        message_type: str = "broadcast"
    ):
        """
        Broadcast a message to all agents.

        Args:
            content: Message content
            message_type: Type of message
        """
        for agent_id in self.agents:
            message = AgentMessage(
                content=content,
                sender=self.coordinator_id,
                receiver=agent_id,
                message_type=message_type
            )
            await self.send_message(message)

    def get_coordinator_info(self) -> Dict[str, Any]:
        """Get coordinator information."""
        return {
            "coordinator_id": self.coordinator_id,
            "agents": list(self.agents.keys()),
            "agent_status": self.get_agent_status(),
            "active_workflows": len(self.workflows),
            "message_queue_size": self.message_queue.qsize()
        }
