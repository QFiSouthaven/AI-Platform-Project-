"""
Code generation agent for multi-agent coordination.

Specialized agent for code generation tasks with memory and planning capabilities.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from app.models.llm_models import (
    GenerationRequest,
    GenerationResponse,
    InferenceConfig,
    ProgrammingLanguage,
    TaskType,
)
from app.services.code_generator import CodeGeneratorService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class AgentState(str, Enum):
    """Agent execution states."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentMessage:
    """Message for agent communication."""

    def __init__(
        self,
        content: str,
        sender: str,
        receiver: str,
        message_type: str = "task",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.content = content
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class CodeAgent:
    """
    Specialized agent for code generation tasks.

    Features:
    - Task planning and decomposition
    - Iterative refinement
    - Self-review and correction
    - Context management
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGeneratorService(llm_service)
        self.agent_id = f"code_agent_{uuid.uuid4().hex[:8]}"
        self.state = AgentState.IDLE
        self.memory: List[Dict[str, Any]] = []
        self.max_iterations = 3

    async def execute(
        self,
        task: str,
        language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
        context: Optional[str] = None,
        requirements: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a code generation task.

        Args:
            task: Task description
            language: Target programming language
            context: Additional context
            requirements: Specific requirements
            correlation_id: Request correlation ID

        Returns:
            Dict with generated code and execution details
        """
        self.state = AgentState.PLANNING
        execution_id = correlation_id or str(uuid.uuid4())

        logger.info(
            "Code agent starting task",
            agent_id=self.agent_id,
            task=task[:100],
            execution_id=execution_id
        )

        try:
            # Step 1: Plan the task
            plan = await self._plan_task(task, language, requirements)

            # Step 2: Execute generation
            self.state = AgentState.EXECUTING
            result = await self._execute_generation(
                task, language, context, requirements, plan
            )

            # Step 3: Review and refine
            self.state = AgentState.REVIEWING
            refined_result = await self._review_and_refine(
                result, task, language, requirements
            )

            # Store in memory
            self._add_to_memory({
                "task": task,
                "language": language,
                "result": refined_result,
                "execution_id": execution_id
            })

            self.state = AgentState.COMPLETED

            logger.info(
                "Code agent completed task",
                agent_id=self.agent_id,
                execution_id=execution_id,
                iterations=refined_result.get("iterations", 1)
            )

            return {
                "agent_id": self.agent_id,
                "execution_id": execution_id,
                "code": refined_result["code"],
                "language": language,
                "plan": plan,
                "iterations": refined_result.get("iterations", 1),
                "review_notes": refined_result.get("review_notes", []),
                "state": self.state
            }

        except Exception as e:
            self.state = AgentState.FAILED
            logger.error(
                "Code agent failed",
                agent_id=self.agent_id,
                error=str(e),
                execution_id=execution_id
            )
            raise

    async def _plan_task(
        self,
        task: str,
        language: ProgrammingLanguage,
        requirements: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Plan the code generation task.

        Args:
            task: Task description
            language: Programming language
            requirements: Specific requirements

        Returns:
            Execution plan
        """
        planning_prompt = f"""You are a senior {language.value} developer planning a code implementation.

Task: {task}

Requirements:
{chr(10).join(f'- {r}' for r in (requirements or ['None specified']))}

Create a brief implementation plan:
1. Key components needed
2. Data structures to use
3. Main functions/classes
4. Edge cases to handle

Respond concisely with the plan:"""

        result = await self.llm_service.generate(
            prompt=planning_prompt,
            config=InferenceConfig(temperature=0.5, max_length=500)
        )

        return {
            "plan_text": result["text"],
            "language": language,
            "requirements": requirements
        }

    async def _execute_generation(
        self,
        task: str,
        language: ProgrammingLanguage,
        context: Optional[str],
        requirements: Optional[List[str]],
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the code generation.

        Args:
            task: Task description
            language: Programming language
            context: Additional context
            requirements: Specific requirements
            plan: Execution plan

        Returns:
            Generation result
        """
        # Enhance prompt with plan
        enhanced_prompt = f"{task}\n\nImplementation approach:\n{plan['plan_text']}"

        request = GenerationRequest(
            prompt=enhanced_prompt,
            language=language,
            task_type=TaskType.FUNCTION,
            context=context,
            requirements=requirements,
            config=InferenceConfig(temperature=0.7, max_length=2048)
        )

        response = await self.code_generator.generate(request)

        return {
            "code": response.code,
            "tokens_used": response.tokens_used,
            "generation_time_ms": response.generation_time_ms
        }

    async def _review_and_refine(
        self,
        result: Dict[str, Any],
        task: str,
        language: ProgrammingLanguage,
        requirements: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Review generated code and refine if needed.

        Args:
            result: Initial generation result
            task: Original task
            language: Programming language
            requirements: Requirements

        Returns:
            Refined result
        """
        code = result["code"]
        review_notes = []
        iterations = 1

        for i in range(self.max_iterations - 1):
            # Self-review prompt
            review_prompt = f"""Review this {language.value} code for the task: {task}

Code:
```{language.value}
{code}
```

Requirements:
{chr(10).join(f'- {r}' for r in (requirements or ['None specified']))}

Identify issues:
1. Does it meet all requirements?
2. Are there bugs or errors?
3. Can it be improved?

If issues found, provide corrected code. If code is good, respond with "APPROVED".
"""

            review_result = await self.llm_service.generate(
                prompt=review_prompt,
                config=InferenceConfig(temperature=0.3, max_length=2048)
            )

            review_text = review_result["text"]
            review_notes.append(review_text[:200])

            # Check if approved
            if "APPROVED" in review_text.upper():
                break

            # Extract improved code if present
            import re
            code_match = re.search(
                r'```(?:\w+)?\s*(.*?)```',
                review_text,
                re.DOTALL
            )
            if code_match:
                code = code_match.group(1).strip()
                iterations += 1
            else:
                break

        result["code"] = code
        result["iterations"] = iterations
        result["review_notes"] = review_notes

        return result

    def _add_to_memory(self, entry: Dict[str, Any]):
        """Add entry to agent memory."""
        entry["timestamp"] = datetime.utcnow().isoformat()
        self.memory.append(entry)

        # Keep memory bounded
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state

    def get_memory(self) -> List[Dict[str, Any]]:
        """Get agent memory."""
        return self.memory

    async def receive_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Receive and process a message from another agent.

        Args:
            message: Incoming message

        Returns:
            Response message or None
        """
        logger.debug(
            "Code agent received message",
            agent_id=self.agent_id,
            sender=message.sender,
            message_type=message.message_type
        )

        if message.message_type == "task":
            # Execute the task
            result = await self.execute(
                task=message.content,
                language=message.metadata.get("language", ProgrammingLanguage.PYTHON),
                context=message.metadata.get("context"),
                requirements=message.metadata.get("requirements")
            )

            return AgentMessage(
                content=result["code"],
                sender=self.agent_id,
                receiver=message.sender,
                message_type="result",
                metadata={"execution_id": result["execution_id"]}
            )

        elif message.message_type == "query":
            # Answer a query about capabilities or status
            return AgentMessage(
                content=f"Agent {self.agent_id} is {self.state}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="response"
            )

        return None
