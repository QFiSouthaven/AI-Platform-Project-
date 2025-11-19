"""
API endpoints for code evaluation.
"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.evaluation import (
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    ComparisonRequest,
    ComparisonResponse,
    EvaluationRequest,
    EvaluationResponse,
)
from app.models.llm_models import ProgrammingLanguage
from app.services.evaluator import EvaluatorService
from app.services.llm_service import LLMService

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from app state."""
    from app.main import get_llm_service
    return get_llm_service()


@router.post(
    "/",
    response_model=EvaluationResponse,
    summary="Evaluate code",
    description="Evaluate code quality and provide metrics, scores, and suggestions"
)
async def evaluate_code(
    request: EvaluationRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> EvaluationResponse:
    """
    Evaluate code quality.

    - **code**: The code to evaluate
    - **language**: Programming language
    - **evaluation_criteria**: Specific criteria to evaluate
    - **include_suggestions**: Whether to include improvement suggestions
    """
    try:
        evaluator = EvaluatorService(llm_service)
        response = await evaluator.evaluate(request)
        return response

    except Exception as e:
        logger.error(
            "Code evaluation failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code evaluation failed: {str(e)}"
        )


@router.post(
    "/quick",
    summary="Quick evaluation",
    description="Get a quick quality score for code"
)
async def quick_evaluate(
    code: str,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    llm_service: LLMService = Depends(get_llm_service)
) -> dict:
    """
    Get a quick quality assessment.

    - **code**: The code to evaluate
    - **language**: Programming language
    """
    try:
        evaluator = EvaluatorService(llm_service)

        request = EvaluationRequest(
            code=code,
            language=language,
            include_suggestions=False
        )

        response = await evaluator.evaluate(request)

        return {
            "quality_level": response.quality_level,
            "overall_score": response.scores.overall,
            "summary": response.summary,
            "issues_count": len(response.issues)
        }

    except Exception as e:
        logger.error("Quick evaluation failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Quick evaluation failed: {str(e)}"
        )


@router.post(
    "/compare",
    response_model=ComparisonResponse,
    summary="Compare code versions",
    description="Compare two versions of code for quality differences"
)
async def compare_code(
    request: ComparisonRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> ComparisonResponse:
    """
    Compare two versions of code.

    - **original_code**: The original code
    - **modified_code**: The modified code
    - **language**: Programming language
    """
    try:
        evaluator = EvaluatorService(llm_service)

        # Evaluate both versions
        original_request = EvaluationRequest(
            code=request.original_code,
            language=request.language,
            include_suggestions=False
        )
        modified_request = EvaluationRequest(
            code=request.modified_code,
            language=request.language,
            include_suggestions=False
        )

        import asyncio
        import time

        start_time = time.time()
        original_result, modified_result = await asyncio.gather(
            evaluator.evaluate(original_request),
            evaluator.evaluate(modified_request)
        )

        # Compare results
        improvements = []
        regressions = []

        score_fields = [
            "overall", "readability", "maintainability",
            "performance", "security", "best_practices", "documentation"
        ]

        for field in score_fields:
            orig_score = getattr(original_result.scores, field)
            mod_score = getattr(modified_result.scores, field)
            diff = mod_score - orig_score

            if diff > 0.5:
                improvements.append(f"{field.capitalize()}: +{diff:.1f}")
            elif diff < -0.5:
                regressions.append(f"{field.capitalize()}: {diff:.1f}")

        # Determine overall change
        overall_diff = modified_result.scores.overall - original_result.scores.overall
        if overall_diff > 0.5:
            overall_change = "improved"
        elif overall_diff < -0.5:
            overall_change = "degraded"
        else:
            overall_change = "unchanged"

        # Generate recommendation
        if overall_change == "improved":
            recommendation = "The modified code shows improvement. Consider adopting these changes."
        elif overall_change == "degraded":
            recommendation = "The modified code shows regression. Review the changes carefully."
        else:
            recommendation = "The changes have minimal impact on overall quality."

        comparison_time = (time.time() - start_time) * 1000

        return ComparisonResponse(
            status="success",
            original_scores=original_result.scores,
            modified_scores=modified_result.scores,
            improvements=improvements,
            regressions=regressions,
            overall_change=overall_change,
            recommendation=recommendation,
            comparison_time_ms=comparison_time,
            correlation_id=request.correlation_id
        )

    except Exception as e:
        logger.error(
            "Code comparison failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Code comparison failed: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=BatchEvaluationResponse,
    summary="Batch evaluate",
    description="Evaluate multiple code files"
)
async def batch_evaluate(
    request: BatchEvaluationRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> BatchEvaluationResponse:
    """
    Evaluate multiple code files in batch.

    - **files**: List of {filename, code, language} objects
    - **evaluation_criteria**: Criteria for evaluation
    - **include_suggestions**: Whether to include suggestions
    """
    if len(request.files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files per batch"
        )

    try:
        import time
        start_time = time.time()

        evaluator = EvaluatorService(llm_service)
        results = []
        total_issues = 0
        total_suggestions = 0

        # Aggregate scores
        score_sums = {
            "overall": 0, "readability": 0, "maintainability": 0,
            "performance": 0, "security": 0, "best_practices": 0, "documentation": 0
        }

        for file_info in request.files:
            eval_request = EvaluationRequest(
                code=file_info.get("code", ""),
                language=file_info.get("language", ProgrammingLanguage.PYTHON),
                evaluation_criteria=request.evaluation_criteria,
                include_suggestions=request.include_suggestions
            )

            response = await evaluator.evaluate(eval_request)

            results.append({
                "filename": file_info.get("filename", "unknown"),
                "quality_level": response.quality_level,
                "scores": response.scores.model_dump(),
                "issues_count": len(response.issues),
                "suggestions_count": len(response.suggestions)
            })

            total_issues += len(response.issues)
            total_suggestions += len(response.suggestions)

            for key in score_sums:
                score_sums[key] += getattr(response.scores, key)

        # Calculate aggregate scores
        num_files = len(request.files)
        from app.models.evaluation import QualityScore
        aggregate_scores = QualityScore(
            overall=score_sums["overall"] / num_files,
            readability=score_sums["readability"] / num_files,
            maintainability=score_sums["maintainability"] / num_files,
            performance=score_sums["performance"] / num_files,
            security=score_sums["security"] / num_files,
            best_practices=score_sums["best_practices"] / num_files,
            documentation=score_sums["documentation"] / num_files
        )

        evaluation_time = (time.time() - start_time) * 1000

        return BatchEvaluationResponse(
            status="success",
            results=results,
            aggregate_scores=aggregate_scores,
            total_issues=total_issues,
            total_suggestions=total_suggestions,
            evaluation_time_ms=evaluation_time,
            correlation_id=request.correlation_id
        )

    except Exception as e:
        logger.error(
            "Batch evaluation failed",
            error=str(e),
            correlation_id=request.correlation_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Batch evaluation failed: {str(e)}"
        )


@router.get(
    "/criteria",
    response_model=List[str],
    summary="List evaluation criteria",
    description="Get list of available evaluation criteria"
)
async def list_criteria() -> List[str]:
    """Get list of available evaluation criteria."""
    return [
        "readability",
        "maintainability",
        "performance",
        "security",
        "best_practices",
        "documentation",
        "error_handling",
        "testing"
    ]
