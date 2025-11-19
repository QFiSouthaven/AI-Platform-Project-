"""
Debugging agent for multi-agent coordination.

Specialized agent for code debugging and error analysis.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog

from app.agents.code_agent import AgentMessage, AgentState
from app.models.llm_models import (
    DebugRequest,
    InferenceConfig,
    ProgrammingLanguage,
)
from app.services.debugger import DebuggerService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)


class DebugAgent:
    """
    Specialized agent for code debugging tasks.

    Features:
    - Error analysis and diagnosis
    - Bug detection and fixing
    - Root cause analysis
    - Test suggestion
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.debugger = DebuggerService(llm_service)
        self.agent_id = f"debug_agent_{uuid.uuid4().hex[:8]}"
        self.state = AgentState.IDLE
        self.memory: List[Dict[str, Any]] = []
        self.known_patterns: Dict[str, str] = {}

    async def execute(
        self,
        code: str,
        language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a debugging task.

        Args:
            code: Code to debug
            language: Programming language
            error_message: Error message if available
            stack_trace: Stack trace if available
            correlation_id: Request correlation ID

        Returns:
            Dict with debugging results
        """
        self.state = AgentState.PLANNING
        execution_id = correlation_id or str(uuid.uuid4())

        logger.info(
            "Debug agent starting task",
            agent_id=self.agent_id,
            has_error=bool(error_message),
            execution_id=execution_id
        )

        try:
            # Step 1: Analyze the problem
            analysis = await self._analyze_problem(
                code, language, error_message, stack_trace
            )

            # Step 2: Debug and fix
            self.state = AgentState.EXECUTING
            debug_result = await self._debug_code(
                code, language, error_message, stack_trace, analysis
            )

            # Step 3: Verify fix
            self.state = AgentState.REVIEWING
            verification = await self._verify_fix(
                debug_result["fixed_code"],
                code,
                language,
                error_message
            )

            # Store in memory
            self._add_to_memory({
                "code": code,
                "language": language,
                "error": error_message,
                "result": debug_result,
                "execution_id": execution_id
            })

            self.state = AgentState.COMPLETED

            logger.info(
                "Debug agent completed task",
                agent_id=self.agent_id,
                bugs_found=len(debug_result.get("bugs_found", [])),
                execution_id=execution_id
            )

            return {
                "agent_id": self.agent_id,
                "execution_id": execution_id,
                "fixed_code": debug_result["fixed_code"],
                "bugs_found": debug_result["bugs_found"],
                "analysis": analysis,
                "verification": verification,
                "state": self.state
            }

        except Exception as e:
            self.state = AgentState.FAILED
            logger.error(
                "Debug agent failed",
                agent_id=self.agent_id,
                error=str(e),
                execution_id=execution_id
            )
            raise

    async def _analyze_problem(
        self,
        code: str,
        language: ProgrammingLanguage,
        error_message: Optional[str],
        stack_trace: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze the problem before debugging.

        Args:
            code: Code to analyze
            language: Programming language
            error_message: Error message
            stack_trace: Stack trace

        Returns:
            Analysis results
        """
        analysis_prompt = f"""Analyze this {language.value} code problem:

Code:
```{language.value}
{code}
```

"""
        if error_message:
            analysis_prompt += f"Error: {error_message}\n"
        if stack_trace:
            analysis_prompt += f"Stack Trace:\n{stack_trace}\n"

        analysis_prompt += """
Provide:
1. Problem category (syntax, logic, runtime, type error, etc.)
2. Likely root cause
3. Affected components
4. Severity assessment
"""

        result = await self.llm_service.generate(
            prompt=analysis_prompt,
            config=InferenceConfig(temperature=0.3, max_length=500)
        )

        # Check for known patterns
        pattern_match = self._check_known_patterns(error_message or "")

        return {
            "analysis_text": result["text"],
            "known_pattern": pattern_match,
            "has_error": bool(error_message)
        }

    async def _debug_code(
        self,
        code: str,
        language: ProgrammingLanguage,
        error_message: Optional[str],
        stack_trace: Optional[str],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Debug the code and provide fixes.

        Args:
            code: Code to debug
            language: Programming language
            error_message: Error message
            stack_trace: Stack trace
            analysis: Problem analysis

        Returns:
            Debug result
        """
        request = DebugRequest(
            code=code,
            language=language,
            error_message=error_message,
            stack_trace=stack_trace,
            config=InferenceConfig(temperature=0.3, max_length=3000)
        )

        response = await self.debugger.debug(request)

        return {
            "fixed_code": response.fixed_code,
            "bugs_found": [bug.model_dump() for bug in response.bugs_found],
            "debug_analysis": response.analysis,
            "tokens_used": response.tokens_used
        }

    async def _verify_fix(
        self,
        fixed_code: str,
        original_code: str,
        language: ProgrammingLanguage,
        original_error: Optional[str]
    ) -> Dict[str, Any]:
        """
        Verify that the fix addresses the issue.

        Args:
            fixed_code: The fixed code
            original_code: Original problematic code
            language: Programming language
            original_error: Original error message

        Returns:
            Verification result
        """
        verify_prompt = f"""Verify this {language.value} code fix:

Original Code:
```{language.value}
{original_code}
```

Fixed Code:
```{language.value}
{fixed_code}
```

Original Error: {original_error or 'Not specified'}

Verify:
1. Does the fix address the original issue?
2. Does the fix introduce new issues?
3. Is the fix correct and complete?

Respond with: VERIFIED (if good) or ISSUES: [list issues]
"""

        result = await self.llm_service.generate(
            prompt=verify_prompt,
            config=InferenceConfig(temperature=0.2, max_length=300)
        )

        is_verified = "VERIFIED" in result["text"].upper()

        return {
            "is_verified": is_verified,
            "verification_notes": result["text"],
            "confidence": "high" if is_verified else "medium"
        }

    def _check_known_patterns(self, error_message: str) -> Optional[str]:
        """
        Check if error matches known patterns.

        Args:
            error_message: Error message to check

        Returns:
            Pattern name if matched
        """
        patterns = {
            "null_pointer": ["NullPointerException", "None has no attribute", "undefined is not"],
            "index_out_of_bounds": ["IndexError", "ArrayIndexOutOfBoundsException", "index out of range"],
            "type_error": ["TypeError", "cannot convert", "expected str"],
            "import_error": ["ImportError", "ModuleNotFoundError", "cannot find module"],
            "syntax_error": ["SyntaxError", "unexpected token", "invalid syntax"],
            "division_by_zero": ["ZeroDivisionError", "division by zero", "divide by zero"]
        }

        error_lower = error_message.lower()
        for pattern_name, keywords in patterns.items():
            if any(kw.lower() in error_lower for kw in keywords):
                return pattern_name

        return None

    def _add_to_memory(self, entry: Dict[str, Any]):
        """Add entry to agent memory."""
        entry["timestamp"] = datetime.utcnow().isoformat()
        self.memory.append(entry)

        # Keep memory bounded
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

        # Learn patterns
        if entry.get("error"):
            self._learn_pattern(entry)

    def _learn_pattern(self, entry: Dict[str, Any]):
        """Learn from debugging experience."""
        error = entry.get("error", "")
        result = entry.get("result", {})

        if error and result.get("fixed_code"):
            # Store simplified pattern
            error_type = error.split(":")[0] if ":" in error else error[:50]
            self.known_patterns[error_type] = result.get("debug_analysis", "")[:200]

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
            "Debug agent received message",
            agent_id=self.agent_id,
            sender=message.sender,
            message_type=message.message_type
        )

        if message.message_type == "task":
            # Execute debugging task
            result = await self.execute(
                code=message.content,
                language=message.metadata.get("language", ProgrammingLanguage.PYTHON),
                error_message=message.metadata.get("error_message"),
                stack_trace=message.metadata.get("stack_trace")
            )

            return AgentMessage(
                content=result["fixed_code"],
                sender=self.agent_id,
                receiver=message.sender,
                message_type="result",
                metadata={
                    "execution_id": result["execution_id"],
                    "bugs_found": len(result["bugs_found"])
                }
            )

        elif message.message_type == "analyze":
            # Just analyze without fixing
            analysis = await self._analyze_problem(
                message.content,
                message.metadata.get("language", ProgrammingLanguage.PYTHON),
                message.metadata.get("error_message"),
                message.metadata.get("stack_trace")
            )

            return AgentMessage(
                content=analysis["analysis_text"],
                sender=self.agent_id,
                receiver=message.sender,
                message_type="analysis"
            )

        return None

    async def suggest_prevention(
        self,
        bug_type: str,
        language: ProgrammingLanguage
    ) -> str:
        """
        Suggest how to prevent a type of bug.

        Args:
            bug_type: Type of bug
            language: Programming language

        Returns:
            Prevention suggestions
        """
        prompt = f"""Provide best practices to prevent {bug_type} bugs in {language.value}.

Include:
1. Coding patterns to follow
2. Common mistakes to avoid
3. Tools or linters that help
4. Example of correct code

Be concise and practical:"""

        result = await self.llm_service.generate(
            prompt=prompt,
            config=InferenceConfig(temperature=0.4, max_length=500)
        )

        return result["text"]
