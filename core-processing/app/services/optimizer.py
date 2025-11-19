"""
Code optimization service using LLM.

Analyzes and optimizes code for performance, readability, and best practices.
"""

import re
import time
from typing import List, Optional

import structlog

from app.models.llm_models import (
    InferenceConfig,
    Optimization,
    OptimizationRequest,
    OptimizationResponse,
    ProgrammingLanguage,
)
from app.services.llm_service import LLMService
from app.utils.code_parser import CodeParser
from app.utils.prompt_templates import PromptTemplates

logger = structlog.get_logger(__name__)


class OptimizerService:
    """
    Service for code optimization using LLM.

    Supports:
    - Performance optimization
    - Readability improvements
    - Memory optimization
    - Security hardening
    - Best practices enforcement
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompt_templates = PromptTemplates()
        self.code_parser = CodeParser()

    async def optimize(
        self,
        request: OptimizationRequest
    ) -> OptimizationResponse:
        """
        Optimize code based on the request.

        Args:
            request: Optimization request with code and goals

        Returns:
            OptimizationResponse with optimized code
        """
        start_time = time.time()

        logger.info(
            "Starting code optimization",
            language=request.language,
            goals=request.optimization_goals,
            correlation_id=request.correlation_id
        )

        try:
            # Build optimization prompt
            prompt = self._build_optimization_prompt(request)

            # Configure inference
            config = request.config or InferenceConfig(
                temperature=0.4,
                max_length=4096
            )

            # Generate optimizations
            result = await self.llm_service.generate(
                prompt=prompt,
                config=config,
                stop_sequences=["```\n\n", "---END---"]
            )

            # Parse the response
            optimized_code, optimizations, summary = self._parse_optimization_response(
                result["text"],
                request.code,
                request.language
            )

            optimization_time = (time.time() - start_time) * 1000

            response = OptimizationResponse(
                status="success",
                optimized_code=optimized_code,
                optimizations=optimizations,
                summary=summary,
                tokens_used=result["tokens_used"],
                optimization_time_ms=optimization_time,
                model_name=result["model_name"],
                correlation_id=request.correlation_id
            )

            logger.info(
                "Code optimization completed",
                optimizations_count=len(optimizations),
                optimization_time_ms=optimization_time,
                correlation_id=request.correlation_id
            )

            return response

        except Exception as e:
            logger.error(
                "Code optimization failed",
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise

    def _build_optimization_prompt(self, request: OptimizationRequest) -> str:
        """
        Build the prompt for optimization.

        Args:
            request: Optimization request

        Returns:
            Formatted prompt string
        """
        parts = []

        # Introduction
        parts.append(
            f"You are an expert {request.language.value} developer. "
            "Optimize the following code for better performance, readability, and maintainability."
        )

        # Add optimization goals
        goals = request.optimization_goals or ["performance", "readability", "best_practices"]
        goals_text = ", ".join(goals)
        parts.append(f"\n## Optimization Goals: {goals_text}")

        # Add preserve behavior note
        if request.preserve_behavior:
            parts.append("\n**Important: Preserve the original behavior of the code.**")

        # Add the code
        parts.append(f"\n## Code to Optimize:\n```{request.language.value}")
        parts.append(request.code)
        parts.append("```\n")

        # Add instructions
        parts.append("""
## Instructions:
1. Analyze the code for optimization opportunities
2. For each optimization, provide:
   - The original code snippet
   - The optimized code snippet
   - Explanation of the improvement
   - Type of improvement (performance, readability, memory, security)
   - Estimated improvement
3. Provide the complete optimized code
4. Provide a summary of all optimizations

## Response Format:
### Summary
[Brief summary of optimizations made]

### Optimizations
[List each optimization with details]

### Optimized Code
```{language}
[Complete optimized code]
```
""".format(language=request.language.value))

        return "\n".join(parts)

    def _parse_optimization_response(
        self,
        response: str,
        original_code: str,
        language: ProgrammingLanguage
    ) -> tuple[str, List[Optimization], str]:
        """
        Parse the LLM optimization response.

        Args:
            response: Raw LLM response
            original_code: Original code
            language: Programming language

        Returns:
            Tuple of (optimized_code, optimizations, summary)
        """
        optimizations = []
        summary = ""
        optimized_code = original_code  # Default to original if parsing fails

        try:
            # Extract summary section
            summary_match = re.search(
                r'### Summary\s*(.*?)(?=### Optimizations|### Optimized|$)',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if summary_match:
                summary = summary_match.group(1).strip()

            # Extract optimizations section
            opts_match = re.search(
                r'### Optimizations\s*(.*?)(?=### Optimized|$)',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if opts_match:
                opts_text = opts_match.group(1)
                optimizations = self._parse_optimizations(opts_text)

            # Extract optimized code
            code_match = re.search(
                r'### Optimized Code\s*```(?:\w+)?\s*(.*?)```',
                response,
                re.DOTALL | re.IGNORECASE
            )
            if code_match:
                optimized_code = code_match.group(1).strip()
            else:
                # Try to find any code block
                code_blocks = re.findall(r'```(?:\w+)?\s*(.*?)```', response, re.DOTALL)
                if code_blocks:
                    optimized_code = code_blocks[-1].strip()

        except Exception as e:
            logger.warning(
                "Failed to parse optimization response",
                error=str(e)
            )
            summary = response[:500] if response else "Unable to optimize code"

        return optimized_code, optimizations, summary

    def _parse_optimizations(self, opts_text: str) -> List[Optimization]:
        """
        Parse optimizations from the response text.

        Args:
            opts_text: Text containing optimization descriptions

        Returns:
            List of Optimization objects
        """
        optimizations = []

        # Split by numbered items
        opt_items = re.split(r'\n(?=\d+\.)', opts_text)

        for item in opt_items:
            if not item.strip():
                continue

            opt = self._parse_single_optimization(item)
            if opt:
                optimizations.append(opt)

        return optimizations

    def _parse_single_optimization(self, opt_text: str) -> Optional[Optimization]:
        """
        Parse a single optimization description.

        Args:
            opt_text: Text describing a single optimization

        Returns:
            Optimization object or None
        """
        try:
            # Extract code snippets
            code_snippets = re.findall(r'`([^`]+)`', opt_text)
            original_code = code_snippets[0] if len(code_snippets) > 0 else ""
            optimized_code = code_snippets[1] if len(code_snippets) > 1 else ""

            # Determine improvement type
            improvement_type = "performance"
            if re.search(r'readab', opt_text, re.IGNORECASE):
                improvement_type = "readability"
            elif re.search(r'memory', opt_text, re.IGNORECASE):
                improvement_type = "memory"
            elif re.search(r'secur', opt_text, re.IGNORECASE):
                improvement_type = "security"

            # Extract estimated improvement
            improvement_match = re.search(
                r'(\d+%|\d+x|faster|slower|better|improved)',
                opt_text,
                re.IGNORECASE
            )
            estimated_improvement = improvement_match.group(1) if improvement_match else None

            # Clean explanation
            explanation = re.sub(r'`[^`]+`', '', opt_text)
            explanation = re.sub(r'\d+\.\s*', '', explanation)
            explanation = explanation.strip()

            if not explanation:
                return None

            return Optimization(
                original_code=original_code,
                optimized_code=optimized_code,
                explanation=explanation[:500],
                improvement_type=improvement_type,
                estimated_improvement=estimated_improvement
            )

        except Exception as e:
            logger.debug(f"Failed to parse optimization: {e}")
            return None

    async def optimize_for_performance(
        self,
        code: str,
        language: ProgrammingLanguage,
        correlation_id: Optional[str] = None
    ) -> OptimizationResponse:
        """
        Optimize code specifically for performance.

        Args:
            code: Code to optimize
            language: Programming language
            correlation_id: Request correlation ID

        Returns:
            OptimizationResponse with performance-optimized code
        """
        request = OptimizationRequest(
            code=code,
            language=language,
            optimization_goals=["performance", "memory"],
            preserve_behavior=True,
            correlation_id=correlation_id
        )
        return await self.optimize(request)

    async def optimize_for_readability(
        self,
        code: str,
        language: ProgrammingLanguage,
        correlation_id: Optional[str] = None
    ) -> OptimizationResponse:
        """
        Optimize code specifically for readability.

        Args:
            code: Code to optimize
            language: Programming language
            correlation_id: Request correlation ID

        Returns:
            OptimizationResponse with readability-optimized code
        """
        request = OptimizationRequest(
            code=code,
            language=language,
            optimization_goals=["readability", "maintainability", "documentation"],
            preserve_behavior=True,
            correlation_id=correlation_id
        )
        return await self.optimize(request)

    async def refactor(
        self,
        code: str,
        language: ProgrammingLanguage,
        refactor_type: str = "general",
        correlation_id: Optional[str] = None
    ) -> OptimizationResponse:
        """
        Refactor code for better structure.

        Args:
            code: Code to refactor
            language: Programming language
            refactor_type: Type of refactoring (general, extract_methods, simplify, etc.)
            correlation_id: Request correlation ID

        Returns:
            OptimizationResponse with refactored code
        """
        prompt = f"""Refactor the following {language.value} code.
Refactoring type: {refactor_type}

Guidelines:
- Extract repeated code into functions
- Simplify complex conditionals
- Improve naming conventions
- Add appropriate comments
- Follow {language.value} best practices

Code:
```{language.value}
{code}
```

Provide the refactored code:
"""

        result = await self.llm_service.generate(
            prompt=prompt,
            config=InferenceConfig(temperature=0.4, max_length=4096)
        )

        # Extract code from response
        code_match = re.search(r'```(?:\w+)?\s*(.*?)```', result["text"], re.DOTALL)
        optimized_code = code_match.group(1).strip() if code_match else result["text"]

        return OptimizationResponse(
            status="success",
            optimized_code=optimized_code,
            optimizations=[],
            summary=f"Code refactored using {refactor_type} strategy",
            tokens_used=result["tokens_used"],
            optimization_time_ms=result["generation_time_ms"],
            model_name=result["model_name"],
            correlation_id=correlation_id
        )
