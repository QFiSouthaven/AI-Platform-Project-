"""
Automated debugging service using LLM.

Analyzes code for bugs, errors, and provides fixes.
"""

import re
import time
from typing import List, Optional

import structlog

from app.models.llm_models import (
    BugFix,
    DebugRequest,
    DebugResponse,
    InferenceConfig,
    ProgrammingLanguage,
)
from app.services.llm_service import LLMService
from app.utils.code_parser import CodeParser
from app.utils.prompt_templates import PromptTemplates

logger = structlog.get_logger(__name__)


class DebuggerService:
    """
    Service for automated code debugging using LLM.

    Supports:
    - Error analysis and explanation
    - Bug detection and fixes
    - Stack trace analysis
    - Code improvement suggestions
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompt_templates = PromptTemplates()
        self.code_parser = CodeParser()

    async def debug(self, request: DebugRequest) -> DebugResponse:
        """
        Debug code and provide fixes.

        Args:
            request: Debug request with code and error information

        Returns:
            DebugResponse with fixed code and bug analysis
        """
        start_time = time.time()

        logger.info(
            "Starting code debugging",
            language=request.language,
            has_error_message=bool(request.error_message),
            has_stack_trace=bool(request.stack_trace),
            correlation_id=request.correlation_id
        )

        try:
            # Build debug prompt
            prompt = self._build_debug_prompt(request)

            # Configure inference
            config = request.config or InferenceConfig(
                temperature=0.3,  # Lower temperature for more precise fixes
                max_length=4096
            )

            # Generate analysis and fixes
            result = await self.llm_service.generate(
                prompt=prompt,
                config=config,
                stop_sequences=["```\n\n", "---END---"]
            )

            # Parse the response
            fixed_code, bugs_found, analysis = self._parse_debug_response(
                result["text"],
                request.code,
                request.language
            )

            debug_time = (time.time() - start_time) * 1000

            response = DebugResponse(
                status="success",
                fixed_code=fixed_code,
                bugs_found=bugs_found,
                analysis=analysis,
                tokens_used=result["tokens_used"],
                debug_time_ms=debug_time,
                model_name=result["model_name"],
                correlation_id=request.correlation_id
            )

            logger.info(
                "Code debugging completed",
                bugs_found=len(bugs_found),
                debug_time_ms=debug_time,
                correlation_id=request.correlation_id
            )

            return response

        except Exception as e:
            logger.error(
                "Code debugging failed",
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise

    def _build_debug_prompt(self, request: DebugRequest) -> str:
        """
        Build the prompt for debugging.

        Args:
            request: Debug request

        Returns:
            Formatted prompt string
        """
        parts = []

        # Introduction
        parts.append(
            f"You are an expert {request.language.value} debugger. "
            "Analyze the following code and identify all bugs and issues."
        )

        # Add the code
        parts.append(f"\n## Code to Debug:\n```{request.language.value}")
        parts.append(request.code)
        parts.append("```\n")

        # Add error message if provided
        if request.error_message:
            parts.append(f"## Error Message:\n{request.error_message}\n")

        # Add stack trace if provided
        if request.stack_trace:
            parts.append(f"## Stack Trace:\n```\n{request.stack_trace}\n```\n")

        # Add expected behavior if provided
        if request.expected_behavior:
            parts.append(f"## Expected Behavior:\n{request.expected_behavior}\n")

        # Add instructions
        parts.append("""
## Instructions:
1. Analyze the code for bugs, errors, and issues
2. For each bug found, provide:
   - Line number (if applicable)
   - The problematic code
   - The fixed code
   - Explanation of the issue
   - Severity (low, medium, high, critical)
3. Provide the complete fixed code
4. Provide an overall analysis

## Response Format:
### Analysis
[Overall analysis of the code issues]

### Bugs Found
[List each bug with details]

### Fixed Code
```{language}
[Complete fixed code]
```
""".format(language=request.language.value))

        return "\n".join(parts)

    def _parse_debug_response(
        self,
        response: str,
        original_code: str,
        language: ProgrammingLanguage
    ) -> tuple[str, List[BugFix], str]:
        """
        Parse the LLM debug response.

        Args:
            response: Raw LLM response
            original_code: Original code
            language: Programming language

        Returns:
            Tuple of (fixed_code, bugs_found, analysis)
        """
        bugs_found = []
        analysis = ""
        fixed_code = original_code  # Default to original if parsing fails

        try:
            # Extract analysis section
            analysis_match = re.search(
                r'### Analysis\s*(.*?)(?=### Bugs|### Fixed|$)',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if analysis_match:
                analysis = analysis_match.group(1).strip()

            # Extract bugs section
            bugs_match = re.search(
                r'### Bugs Found\s*(.*?)(?=### Fixed|$)',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if bugs_match:
                bugs_text = bugs_match.group(1)
                bugs_found = self._parse_bugs(bugs_text)

            # Extract fixed code
            code_match = re.search(
                r'### Fixed Code\s*```(?:\w+)?\s*(.*?)```',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if code_match:
                fixed_code = code_match.group(1).strip()
            else:
                # Try to find any code block
                code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', response, re.DOTALL)
                if code_blocks:
                    fixed_code = code_blocks[-1].strip()

        except Exception as e:
            logger.warning(
                "Failed to parse debug response",
                error=str(e)
            )
            # Return defaults
            analysis = response[:500] if response else "Unable to analyze code"

        return fixed_code, bugs_found, analysis

    def _parse_bugs(self, bugs_text: str) -> List[BugFix]:
        """
        Parse bugs from the response text.

        Args:
            bugs_text: Text containing bug descriptions

        Returns:
            List of BugFix objects
        """
        bugs = []

        # Split by numbered items or bullet points
        bug_items = re.split(r'\n(?=\d+\.|[-*])', bugs_text)

        for item in bug_items:
            if not item.strip():
                continue

            bug = self._parse_single_bug(item)
            if bug:
                bugs.append(bug)

        return bugs

    def _parse_single_bug(self, bug_text: str) -> Optional[BugFix]:
        """
        Parse a single bug description.

        Args:
            bug_text: Text describing a single bug

        Returns:
            BugFix object or None
        """
        try:
            # Extract line number
            line_match = re.search(r'[Ll]ine\s*(\d+)', bug_text)
            line_number = int(line_match.group(1)) if line_match else None

            # Extract severity
            severity = "medium"
            if re.search(r'critical', bug_text, re.IGNORECASE):
                severity = "critical"
            elif re.search(r'high', bug_text, re.IGNORECASE):
                severity = "high"
            elif re.search(r'low', bug_text, re.IGNORECASE):
                severity = "low"

            # Extract code snippets
            code_snippets = re.findall(r'`([^`]+)`', bug_text)
            original_code = code_snippets[0] if len(code_snippets) > 0 else ""
            fixed_code = code_snippets[1] if len(code_snippets) > 1 else ""

            # Clean explanation
            explanation = re.sub(r'`[^`]+`', '', bug_text)
            explanation = re.sub(r'\d+\.\s*', '', explanation)
            explanation = explanation.strip()

            if not explanation:
                return None

            return BugFix(
                line_number=line_number,
                original_code=original_code,
                fixed_code=fixed_code,
                explanation=explanation[:500],
                severity=severity
            )

        except Exception as e:
            logger.debug(f"Failed to parse bug: {e}")
            return None

    async def analyze_error(
        self,
        error_message: str,
        stack_trace: Optional[str] = None,
        language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Analyze an error message and provide explanation.

        Args:
            error_message: The error message
            stack_trace: Optional stack trace
            language: Programming language
            correlation_id: Request correlation ID

        Returns:
            Dict with error analysis
        """
        prompt = f"""Analyze the following {language.value} error and explain:
1. What the error means
2. Common causes
3. How to fix it

Error: {error_message}
"""
        if stack_trace:
            prompt += f"\nStack Trace:\n{stack_trace}"

        result = await self.llm_service.generate(
            prompt=prompt,
            config=InferenceConfig(temperature=0.3, max_length=1024)
        )

        return {
            "error_message": error_message,
            "analysis": result["text"],
            "tokens_used": result["tokens_used"],
            "correlation_id": correlation_id
        }

    async def suggest_tests(
        self,
        code: str,
        language: ProgrammingLanguage,
        correlation_id: Optional[str] = None
    ) -> dict:
        """
        Suggest test cases for the given code.

        Args:
            code: Code to generate tests for
            language: Programming language
            correlation_id: Request correlation ID

        Returns:
            Dict with suggested tests
        """
        prompt = f"""Generate comprehensive test cases for the following {language.value} code.
Include:
1. Unit tests for each function
2. Edge cases
3. Error cases

Code:
```{language.value}
{code}
```

Generate tests using the standard testing framework for {language.value}:
"""

        result = await self.llm_service.generate(
            prompt=prompt,
            config=InferenceConfig(temperature=0.5, max_length=2048)
        )

        return {
            "tests": result["text"],
            "tokens_used": result["tokens_used"],
            "correlation_id": correlation_id
        }
