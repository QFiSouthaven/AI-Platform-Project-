"""
API endpoints for code debugging.
"""

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.llm_models import (
    DebugRequest,
    DebugResponse,
    ProgrammingLanguage,
)
from app.services.debugger import DebuggerService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from app state."""
    from app.main import get_llm_service
    return get_llm_service()


@router.post(
    "/",
    response_model=DebugResponse,
    summary="Debug code",
    description="Analyze code for bugs and provide fixes"
)
async def debug_code(
    request: DebugRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> DebugResponse:
    """
    Debug code and provide fixes.

    - **code**: The code to debug
    - **language**: Programming language
    - **error_message**: Error message if available
    - **stack_trace**: Stack trace if available
    - **expected_behavior**: Description of expected behavior
    - **config**: Inference configuration
    """
    try:
        debugger = DebuggerService(llm_service)
        response = await debugger.debug(request)
        return response

    except Exception as e:
        logger.error(
            "Code debugging failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code debugging failed: {str(e)}"
        )


@router.post(
    "/analyze-error",
    summary="Analyze error",
    description="Analyze an error message and provide explanation"
)
async def analyze_error(
    error_message: str,
    stack_trace: Optional[str] = None,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> dict:
    """
    Analyze an error message.

    - **error_message**: The error message to analyze
    - **stack_trace**: Optional stack trace
    - **language**: Programming language
    """
    try:
        debugger = DebuggerService(llm_service)
        result = await debugger.analyze_error(
            error_message=error_message,
            stack_trace=stack_trace,
            language=language,
            correlation_id=correlation_id
        )
        return result

    except Exception as e:
        logger.error(
            "Error analysis failed",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error analysis failed: {str(e)}"
        )


@router.post(
    "/suggest-tests",
    summary="Suggest tests",
    description="Suggest test cases for the given code"
)
async def suggest_tests(
    code: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> dict:
    """
    Suggest test cases for code.

    - **code**: The code to generate tests for
    - **language**: Programming language
    """
    try:
        debugger = DebuggerService(llm_service)
        result = await debugger.suggest_tests(
            code=code,
            language=language,
            correlation_id=correlation_id
        )
        return result

    except Exception as e:
        logger.error(
            "Test suggestion failed",
            error=str(e),
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Test suggestion failed: {str(e)}"
        )


@router.post(
    "/fix-specific",
    summary="Fix specific issue",
    description="Fix a specific type of issue in the code"
)
async def fix_specific_issue(
    code: str,
    issue_type: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    correlation_id: Optional[str] = None,
    llm_service: LLMService = Depends(get_llm_service)
) -> dict:
    """
    Fix a specific type of issue.

    - **code**: The code to fix
    - **issue_type**: Type of issue to fix (e.g., "null_check", "error_handling")
    - **language**: Programming language
    """
    try:
        debugger = DebuggerService(llm_service)

        # Create a targeted debug request
        request = DebugRequest(
            code=code,
            language=language,
            expected_behavior=f"Fix {issue_type} issues",
            correlation_id=correlation_id
        )

        response = await debugger.debug(request)

        return {
            "fixed_code": response.fixed_code,
            "issue_type": issue_type,
            "bugs_found": [bug.model_dump() for bug in response.bugs_found],
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(
            "Specific fix failed",
            error=str(e),
            issue_type=issue_type,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Specific fix failed: {str(e)}"
        )


@router.post(
    "/batch",
    summary="Batch debug",
    description="Debug multiple code snippets"
)
async def batch_debug(
    requests: list[DebugRequest],
    llm_service: LLMService = Depends(get_llm_service)
) -> list[DebugResponse]:
    """
    Debug multiple code snippets in batch.

    - **requests**: List of debug requests
    """
    if len(requests) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 requests per batch"
        )

    try:
        debugger = DebuggerService(llm_service)
        responses = []

        for request in requests:
            response = await debugger.debug(request)
            responses.append(response)

        return responses

    except Exception as e:
        logger.error("Batch debug failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Batch debug failed: {str(e)}"
        )
