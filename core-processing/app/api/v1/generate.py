"""
API endpoints for code generation.
"""

from typing import Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.models.llm_models import (
    GenerationRequest,
    GenerationResponse,
    InferenceConfig,
    ModelInfo,
    ProgrammingLanguage,
    TaskType,
)
from app.services.code_generator import CodeGeneratorService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from app state."""
    from app.main import get_llm_service
    return get_llm_service()


@router.post(
    "/",
    response_model=GenerationResponse,
    summary="Generate code",
    description="Generate code based on a natural language prompt"
)
async def generate_code(
    request: GenerationRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> GenerationResponse:
    """
    Generate code based on a natural language description.

    - **prompt**: Natural language description of what to generate
    - **language**: Target programming language
    - **task_type**: Type of code to generate (function, class, etc.)
    - **context**: Additional context for generation
    - **requirements**: Specific requirements for the code
    - **config**: Inference configuration (temperature, max_length, etc.)
    """
    try:
        generator = CodeGeneratorService(llm_service)
        response = await generator.generate(request)
        return response

    except Exception as e:
        logger.error(
            "Code generation failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code generation failed: {str(e)}"
        )


@router.post(
    "/complete",
    response_model=GenerationResponse,
    summary="Complete code",
    description="Complete partial code"
)
async def complete_code(
    code_prefix: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> GenerationResponse:
    """
    Complete partial code.

    - **code_prefix**: The beginning of the code to complete
    - **language**: Programming language
    """
    try:
        generator = CodeGeneratorService(llm_service)
        response = await generator.complete_code(
            code_prefix=code_prefix,
            language=language,
            correlation_id=correlation_id
        )
        return response

    except Exception as e:
        logger.error(
            "Code completion failed",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code completion failed: {str(e)}"
        )


@router.post(
    "/with-examples",
    response_model=GenerationResponse,
    summary="Generate with examples",
    description="Generate code using few-shot learning with examples"
)
async def generate_with_examples(
    request: GenerationRequest,
    examples: List[Dict[str, str]],
    llm_service: LLMService = Depends(get_llm_service)
) -> GenerationResponse:
    """
    Generate code using few-shot examples.

    - **request**: Generation request
    - **examples**: List of {input, output} example pairs
    """
    try:
        generator = CodeGeneratorService(llm_service)
        response = await generator.generate_with_examples(request, examples)
        return response

    except Exception as e:
        logger.error(
            "Few-shot generation failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Few-shot generation failed: {str(e)}"
        )


@router.get(
    "/model-info",
    response_model=Optional[ModelInfo],
    summary="Get model info",
    description="Get information about the loaded LLM model"
)
async def get_model_info(
    llm_service: LLMService = Depends(get_llm_service)
) -> Optional[ModelInfo]:
    """Get information about the currently loaded model."""
    return llm_service.get_model_info()


@router.post(
    "/batch",
    response_model=List[GenerationResponse],
    summary="Batch generate",
    description="Generate code for multiple prompts"
)
async def batch_generate(
    requests: List[GenerationRequest],
    llm_service: LLMService = Depends(get_llm_service)
) -> List[GenerationResponse]:
    """
    Generate code for multiple prompts in batch.

    - **requests**: List of generation requests
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 requests per batch"
        )

    try:
        generator = CodeGeneratorService(llm_service)
        responses = []

        for request in requests:
            response = await generator.generate(request)
            responses.append(response)

        return responses

    except Exception as e:
        logger.error("Batch generation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch generation failed: {str(e)}"
        )


@router.get(
    "/languages",
    response_model=List[str],
    summary="List supported languages",
    description="Get list of supported programming languages"
)
async def list_languages() -> List[str]:
    """Get list of supported programming languages."""
    return [lang.value for lang in ProgrammingLanguage]


@router.get(
    "/task-types",
    response_model=List[str],
    summary="List task types",
    description="Get list of supported task types"
)
async def list_task_types() -> List[str]:
    """Get list of supported task types."""
    return [task.value for task in TaskType]
