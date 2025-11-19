"""
API endpoints for code optimization.
"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.llm_models import (
    OptimizationRequest,
    OptimizationResponse,
    ProgrammingLanguage,
)
from app.services.llm_service import LLMService
from app.services.optimizer import OptimizerService

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from app state."""
    from app.main import get_llm_service
    return get_llm_service()


@router.post(
    "/",
    response_model=OptimizationResponse,
    summary="Optimize code",
    description="Optimize code for performance, readability, and best practices"
)
async def optimize_code(
    request: OptimizationRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> OptimizationResponse:
    """
    Optimize code based on specified goals.

    - **code**: The code to optimize
    - **language**: Programming language
    - **optimization_goals**: List of goals (performance, readability, memory, security)
    - **preserve_behavior**: Whether to preserve original behavior
    - **config**: Inference configuration
    """
    try:
        optimizer = OptimizerService(llm_service)
        response = await optimizer.optimize(request)
        return response

    except Exception as e:
        logger.error(
            "Code optimization failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code optimization failed: {str(e)}"
        )


@router.post(
    "/performance",
    response_model=OptimizationResponse,
    summary="Optimize for performance",
    description="Optimize code specifically for performance"
)
async def optimize_for_performance(
    code: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> OptimizationResponse:
    """
    Optimize code specifically for performance.

    - **code**: The code to optimize
    - **language**: Programming language
    """
    try:
        optimizer = OptimizerService(llm_service)
        response = await optimizer.optimize_for_performance(
            code=code,
            language=language,
            correlation_id=correlation_id
        )
        return response

    except Exception as e:
        logger.error(
            "Performance optimization failed",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Performance optimization failed: {str(e)}"
        )


@router.post(
    "/readability",
    response_model=OptimizationResponse,
    summary="Optimize for readability",
    description="Optimize code specifically for readability"
)
async def optimize_for_readability(
    code: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> OptimizationResponse:
    """
    Optimize code specifically for readability.

    - **code**: The code to optimize
    - **language**: Programming language
    """
    try:
        optimizer = OptimizerService(llm_service)
        response = await optimizer.optimize_for_readability(
            code=code,
            language=language,
            correlation_id=correlation_id
        )
        return response

    except Exception as e:
        logger.error(
            "Readability optimization failed",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Readability optimization failed: {str(e)}"
        )


@router.post(
    "/refactor",
    response_model=OptimizationResponse,
    summary="Refactor code",
    description="Refactor code for better structure"
)
async def refactor_code(
    code: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    refactor_type: str = "general",
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> OptimizationResponse:
    """
    Refactor code for better structure.

    - **code**: The code to refactor
    - **language**: Programming language
    - **refactor_type**: Type of refactoring (general, extract_methods, simplify)
    """
    try:
        optimizer = OptimizerService(llm_service)
        response = await optimizer.refactor(
            code=code,
            language=language,
            refactor_type=refactor_type,
            correlation_id=correlation_id
        )
        return response

    except Exception as e:
        logger.error(
            "Code refactoring failed",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code refactoring failed: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=List[OptimizationResponse],
    summary="Batch optimize",
    description="Optimize multiple code snippets"
)
async def batch_optimize(
    requests: List[OptimizationRequest],
    llm_service: LLMService = Depends(get_llm_service)
) -> List[OptimizationResponse]:
    """
    Optimize multiple code snippets in batch.

    - **requests**: List of optimization requests
    """
    if len(requests) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 requests per batch"
        )

    try:
        optimizer = OptimizerService(llm_service)
        responses = []

        for request in requests:
            response = await optimizer.optimize(request)
            responses.append(response)

        return responses

    except Exception as e:
        logger.error("Batch optimization failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch optimization failed: {str(e)}"
        )


@router.get(
    "/goals",
    response_model=List[str],
    summary="List optimization goals",
    description="Get list of available optimization goals"
)
async def list_optimization_goals() -> List[str]:
    """Get list of available optimization goals."""
    return [
        "performance",
        "readability",
        "maintainability",
        "memory",
        "security",
        "best_practices",
        "documentation"
    ]
