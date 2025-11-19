"""
Code generation service using LLM.

Provides code generation capabilities for various programming languages and tasks.
"""

import time
from typing import Any, Dict, Optional

import structlog

from app.models.llm_models import (
    GenerationRequest,
    GenerationResponse,
    InferenceConfig,
    ProgrammingLanguage,
    TaskType,
)
from app.services.llm_service import LLMService
from app.utils.prompt_templates import PromptTemplates

logger = structlog.get_logger(__name__)


class CodeGeneratorService:
    """
    Service for generating code using LLM.

    Supports:
    - Multiple programming languages
    - Different task types (function, class, test, etc.)
    - Context-aware generation
    - Customizable inference parameters
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompt_templates = PromptTemplates()

    async def generate(
        self,
        request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate code based on the request.

        Args:
            request: Generation request with prompt and configuration

        Returns:
            GenerationResponse with generated code
        """
        start_time = time.time()

        logger.info(
            "Starting code generation",
            language=request.language,
            task_type=request.task_type,
            correlation_id=request.correlation_id
        )

        try:
            # Build prompt
            prompt = self._build_prompt(request)

            # Get stop sequences for the language
            stop_sequences = self._get_stop_sequences(request.language, request.task_type)

            # Configure inference
            config = request.config or InferenceConfig()

            # Generate code
            result = await self.llm_service.generate(
                prompt=prompt,
                config=config,
                stop_sequences=stop_sequences
            )

            # Post-process generated code
            generated_code = self._post_process_code(
                result["text"],
                request.language,
                request.task_type
            )

            generation_time = (time.time() - start_time) * 1000

            response = GenerationResponse(
                status="success",
                code=generated_code,
                language=request.language,
                tokens_used=result["tokens_used"],
                generation_time_ms=generation_time,
                model_name=result["model_name"],
                correlation_id=request.correlation_id,
                metadata={
                    "task_type": request.task_type,
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"]
                }
            )

            logger.info(
                "Code generation completed",
                language=request.language,
                tokens_used=result["tokens_used"],
                generation_time_ms=generation_time,
                correlation_id=request.correlation_id
            )

            return response

        except Exception as e:
            logger.error(
                "Code generation failed",
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise

    def _build_prompt(self, request: GenerationRequest) -> str:
        """
        Build the prompt for code generation.

        Args:
            request: Generation request

        Returns:
            Formatted prompt string
        """
        # Get base template
        template = self.prompt_templates.get_generation_template(
            request.language,
            request.task_type
        )

        # Build prompt parts
        parts = []

        # Add context if provided
        if request.context:
            parts.append(f"Context:\n{request.context}\n")

        # Add requirements if provided
        if request.requirements:
            requirements_text = "\n".join(f"- {req}" for req in request.requirements)
            parts.append(f"Requirements:\n{requirements_text}\n")

        # Add main prompt
        parts.append(f"Task: {request.prompt}\n")

        # Add template instruction
        parts.append(template)

        return "\n".join(parts)

    def _get_stop_sequences(
        self,
        language: ProgrammingLanguage,
        task_type: TaskType
    ) -> list:
        """
        Get stop sequences for the given language and task type.

        Args:
            language: Programming language
            task_type: Type of code task

        Returns:
            List of stop sequences
        """
        common_stops = ["\n\n\n", "```", "# End", "// End"]

        language_stops = {
            ProgrammingLanguage.PYTHON: ["\nclass ", "\ndef ", "\nif __name__"],
            ProgrammingLanguage.JAVASCRIPT: ["\nfunction ", "\nconst ", "\nclass "],
            ProgrammingLanguage.TYPESCRIPT: ["\nfunction ", "\nconst ", "\nclass ", "\ninterface "],
            ProgrammingLanguage.JAVA: ["\npublic class ", "\nprivate class "],
            ProgrammingLanguage.GO: ["\nfunc ", "\ntype "],
            ProgrammingLanguage.RUST: ["\nfn ", "\nstruct ", "\nimpl "],
        }

        stops = common_stops.copy()
        if language in language_stops:
            stops.extend(language_stops[language])

        return stops

    def _post_process_code(
        self,
        code: str,
        language: ProgrammingLanguage,
        task_type: TaskType
    ) -> str:
        """
        Post-process generated code.

        Args:
            code: Raw generated code
            language: Programming language
            task_type: Type of code task

        Returns:
            Cleaned and formatted code
        """
        # Remove leading/trailing whitespace
        code = code.strip()

        # Remove markdown code blocks if present
        if code.startswith("```"):
            lines = code.split("\n")
            # Find start and end of code block
            start_idx = 1 if lines[0].startswith("```") else 0
            end_idx = len(lines)
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "```":
                    end_idx = i
                    break
            code = "\n".join(lines[start_idx:end_idx])

        # Remove common artifacts
        code = code.replace("```python", "").replace("```javascript", "")
        code = code.replace("```", "")

        # Ensure proper line endings
        code = code.replace("\r\n", "\n").replace("\r", "\n")

        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in code.split("\n")]
        code = "\n".join(lines)

        return code.strip()

    async def generate_with_examples(
        self,
        request: GenerationRequest,
        examples: list[Dict[str, str]]
    ) -> GenerationResponse:
        """
        Generate code using few-shot examples.

        Args:
            request: Generation request
            examples: List of example dicts with 'input' and 'output' keys

        Returns:
            GenerationResponse with generated code
        """
        # Build few-shot prompt
        few_shot_parts = []

        for i, example in enumerate(examples, 1):
            few_shot_parts.append(f"Example {i}:")
            few_shot_parts.append(f"Input: {example['input']}")
            few_shot_parts.append(f"Output:\n{example['output']}\n")

        # Add current request
        few_shot_parts.append("Now generate:")
        few_shot_parts.append(f"Input: {request.prompt}")
        few_shot_parts.append("Output:")

        # Update request prompt
        request.prompt = "\n".join(few_shot_parts)

        return await self.generate(request)

    async def complete_code(
        self,
        code_prefix: str,
        language: ProgrammingLanguage,
        config: Optional[InferenceConfig] = None,
        correlation_id: Optional[str] = None
    ) -> GenerationResponse:
        """
        Complete partial code.

        Args:
            code_prefix: Partial code to complete
            language: Programming language
            config: Inference configuration
            correlation_id: Request correlation ID

        Returns:
            GenerationResponse with completed code
        """
        request = GenerationRequest(
            prompt=code_prefix,
            language=language,
            task_type=TaskType.FUNCTION,
            config=config,
            correlation_id=correlation_id
        )

        # For completion, we use the code prefix directly as the prompt
        result = await self.llm_service.generate(
            prompt=code_prefix,
            config=config or InferenceConfig(),
            stop_sequences=self._get_stop_sequences(language, TaskType.FUNCTION)
        )

        return GenerationResponse(
            status="success",
            code=code_prefix + result["text"],
            language=language,
            tokens_used=result["tokens_used"],
            generation_time_ms=result["generation_time_ms"],
            model_name=result["model_name"],
            correlation_id=correlation_id
        )
