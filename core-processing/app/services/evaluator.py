"""
Code quality evaluation service.

Analyzes code for quality metrics, issues, and provides improvement suggestions.
"""

import ast
import re
import time
from typing import List, Optional

import structlog

from app.models.evaluation import (
    CodeMetrics,
    EvaluationRequest,
    EvaluationResponse,
    Issue,
    QualityLevel,
    QualityScore,
    Suggestion,
)
from app.models.llm_models import InferenceConfig, ProgrammingLanguage
from app.services.llm_service import LLMService
from app.utils.code_parser import CodeParser

logger = structlog.get_logger(__name__)


class EvaluatorService:
    """
    Service for evaluating code quality.

    Provides:
    - Quantitative metrics (complexity, LOC, etc.)
    - Quality scores (readability, maintainability, etc.)
    - Issue detection
    - Improvement suggestions
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_parser = CodeParser()

    async def evaluate(
        self,
        request: EvaluationRequest
    ) -> EvaluationResponse:
        """
        Evaluate code quality.

        Args:
            request: Evaluation request with code

        Returns:
            EvaluationResponse with metrics, scores, and suggestions
        """
        start_time = time.time()

        logger.info(
            "Starting code evaluation",
            language=request.language,
            correlation_id=request.correlation_id
        )

        try:
            # Calculate basic metrics
            metrics = self._calculate_metrics(request.code, request.language)

            # Get LLM-based quality analysis
            llm_analysis = await self._get_llm_analysis(request)

            # Parse LLM response
            scores, issues, suggestions = self._parse_llm_analysis(llm_analysis)

            # Determine overall quality level
            quality_level = self._determine_quality_level(scores.overall)

            evaluation_time = (time.time() - start_time) * 1000

            response = EvaluationResponse(
                status="success",
                quality_level=quality_level,
                scores=scores,
                metrics=metrics,
                issues=issues,
                suggestions=suggestions if request.include_suggestions else [],
                summary=self._generate_summary(scores, issues, suggestions),
                evaluation_time_ms=evaluation_time,
                correlation_id=request.correlation_id
            )

            logger.info(
                "Code evaluation completed",
                quality_level=quality_level,
                overall_score=scores.overall,
                issues_count=len(issues),
                evaluation_time_ms=evaluation_time,
                correlation_id=request.correlation_id
            )

            return response

        except Exception as e:
            logger.error(
                "Code evaluation failed",
                error=str(e),
                correlation_id=request.correlation_id
            )
            raise

    def _calculate_metrics(
        self,
        code: str,
        language: ProgrammingLanguage
    ) -> CodeMetrics:
        """
        Calculate quantitative code metrics.

        Args:
            code: Source code
            language: Programming language

        Returns:
            CodeMetrics with calculated values
        """
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]

        # Count lines of code
        loc = len(non_empty_lines)

        # Count comments
        comment_lines = 0
        if language == ProgrammingLanguage.PYTHON:
            comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
        elif language in [ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.TYPESCRIPT,
                         ProgrammingLanguage.JAVA, ProgrammingLanguage.CPP, ProgrammingLanguage.GO]:
            comment_lines = sum(1 for l in lines if l.strip().startswith('//'))

        comment_ratio = comment_lines / max(loc, 1)

        # Count functions and classes
        num_functions = 0
        num_classes = 0
        cyclomatic = 1
        cognitive = 0

        if language == ProgrammingLanguage.PYTHON:
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        num_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        num_classes += 1
                    elif isinstance(node, (ast.If, ast.While, ast.For)):
                        cyclomatic += 1
                        cognitive += 1
                    elif isinstance(node, ast.ExceptHandler):
                        cyclomatic += 1
                    elif isinstance(node, ast.BoolOp):
                        cyclomatic += len(node.values) - 1
            except SyntaxError:
                pass
        else:
            # Simple regex-based counting for other languages
            num_functions = len(re.findall(r'\bdef\s+\w+|function\s+\w+|\w+\s*\([^)]*\)\s*{', code))
            num_classes = len(re.findall(r'\bclass\s+\w+', code))
            cyclomatic += len(re.findall(r'\bif\b|\bwhile\b|\bfor\b|\bcase\b', code))

        # Calculate maintainability index (simplified)
        # Based on Halstead volume, cyclomatic complexity, and LOC
        maintainability = max(0, min(100, 171 - 5.2 * (cyclomatic / max(num_functions, 1)) - 0.23 * loc + 16.2 * comment_ratio * 10))

        return CodeMetrics(
            lines_of_code=loc,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            number_of_functions=num_functions,
            number_of_classes=num_classes,
            comment_ratio=round(comment_ratio, 2),
            duplicate_code_percentage=0.0,  # Would need more advanced analysis
            maintainability_index=round(maintainability, 1)
        )

    async def _get_llm_analysis(self, request: EvaluationRequest) -> str:
        """
        Get LLM-based code analysis.

        Args:
            request: Evaluation request

        Returns:
            LLM analysis response
        """
        criteria = request.evaluation_criteria or [
            "readability", "maintainability", "performance",
            "security", "best_practices", "documentation"
        ]

        prompt = f"""Evaluate the following {request.language.value} code for quality.

## Evaluation Criteria:
{', '.join(criteria)}

## Code:
```{request.language.value}
{request.code}
```

## Instructions:
Provide a comprehensive evaluation including:

1. **Quality Scores** (0-10 for each):
   - Overall
   - Readability
   - Maintainability
   - Performance
   - Security
   - Best Practices
   - Documentation

2. **Issues Found** (for each issue):
   - Severity (info/warning/error/critical)
   - Category (security/performance/style/bug)
   - Message
   - Line number (if applicable)
   - Suggestion for fix

3. **Improvement Suggestions** (for each):
   - Category
   - Title
   - Description
   - Priority (low/medium/high)
   - Code example (if applicable)

## Response Format:
### Scores
Overall: X/10
Readability: X/10
Maintainability: X/10
Performance: X/10
Security: X/10
Best Practices: X/10
Documentation: X/10

### Issues
[List issues]

### Suggestions
[List suggestions]
"""

        result = await self.llm_service.generate(
            prompt=prompt,
            config=InferenceConfig(temperature=0.3, max_length=3000)
        )

        return result["text"]

    def _parse_llm_analysis(
        self,
        analysis: str
    ) -> tuple[QualityScore, List[Issue], List[Suggestion]]:
        """
        Parse LLM analysis response.

        Args:
            analysis: Raw LLM response

        Returns:
            Tuple of (scores, issues, suggestions)
        """
        # Parse scores
        scores = self._parse_scores(analysis)

        # Parse issues
        issues = self._parse_issues(analysis)

        # Parse suggestions
        suggestions = self._parse_suggestions(analysis)

        return scores, issues, suggestions

    def _parse_scores(self, analysis: str) -> QualityScore:
        """Parse quality scores from analysis."""
        def extract_score(name: str) -> float:
            match = re.search(rf'{name}[:\s]+(\d+(?:\.\d+)?)', analysis, re.IGNORECASE)
            if match:
                return min(10.0, max(0.0, float(match.group(1))))
            return 5.0  # Default

        return QualityScore(
            overall=extract_score('Overall'),
            readability=extract_score('Readability'),
            maintainability=extract_score('Maintainability'),
            performance=extract_score('Performance'),
            security=extract_score('Security'),
            best_practices=extract_score('Best Practices'),
            documentation=extract_score('Documentation')
        )

    def _parse_issues(self, analysis: str) -> List[Issue]:
        """Parse issues from analysis."""
        issues = []

        # Find issues section
        issues_match = re.search(
            r'### Issues\s*(.*?)(?=### Suggestions|$)',
            analysis,
            re.DOTALL | re.IGNORECASE
        )

        if not issues_match:
            return issues

        issues_text = issues_match.group(1)

        # Parse individual issues
        issue_items = re.split(r'\n(?=[-*]|\d+\.)', issues_text)

        for item in issue_items:
            if not item.strip():
                continue

            # Extract severity
            severity = "warning"
            if re.search(r'critical', item, re.IGNORECASE):
                severity = "critical"
            elif re.search(r'error', item, re.IGNORECASE):
                severity = "error"
            elif re.search(r'info', item, re.IGNORECASE):
                severity = "info"

            # Extract category
            category = "style"
            if re.search(r'security', item, re.IGNORECASE):
                category = "security"
            elif re.search(r'performance', item, re.IGNORECASE):
                category = "performance"
            elif re.search(r'bug', item, re.IGNORECASE):
                category = "bug"

            # Extract line number
            line_match = re.search(r'[Ll]ine\s*(\d+)', item)
            line_number = int(line_match.group(1)) if line_match else None

            # Clean message
            message = re.sub(r'[-*]\s*|\d+\.\s*', '', item)
            message = re.sub(r'\([^)]*\)', '', message).strip()

            if message:
                issues.append(Issue(
                    severity=severity,
                    category=category,
                    message=message[:200],
                    line_number=line_number
                ))

        return issues

    def _parse_suggestions(self, analysis: str) -> List[Suggestion]:
        """Parse suggestions from analysis."""
        suggestions = []

        # Find suggestions section
        sugg_match = re.search(
            r'### Suggestions\s*(.*?)$',
            analysis,
            re.DOTALL | re.IGNORECASE
        )

        if not sugg_match:
            return suggestions

        sugg_text = sugg_match.group(1)

        # Parse individual suggestions
        sugg_items = re.split(r'\n(?=[-*]|\d+\.)', sugg_text)

        for item in sugg_items:
            if not item.strip():
                continue

            # Extract priority
            priority = "medium"
            if re.search(r'high', item, re.IGNORECASE):
                priority = "high"
            elif re.search(r'low', item, re.IGNORECASE):
                priority = "low"

            # Determine category
            category = "general"
            if re.search(r'performance', item, re.IGNORECASE):
                category = "performance"
            elif re.search(r'security', item, re.IGNORECASE):
                category = "security"
            elif re.search(r'readability|style', item, re.IGNORECASE):
                category = "readability"

            # Clean description
            description = re.sub(r'[-*]\s*|\d+\.\s*', '', item).strip()

            if description:
                suggestions.append(Suggestion(
                    category=category,
                    title=description[:50],
                    description=description[:300],
                    priority=priority
                ))

        return suggestions

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from score."""
        if score >= 8.5:
            return QualityLevel.EXCELLENT
        elif score >= 7.0:
            return QualityLevel.GOOD
        elif score >= 5.0:
            return QualityLevel.FAIR
        elif score >= 3.0:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _generate_summary(
        self,
        scores: QualityScore,
        issues: List[Issue],
        suggestions: List[Suggestion]
    ) -> str:
        """Generate evaluation summary."""
        critical_issues = sum(1 for i in issues if i.severity == "critical")
        error_issues = sum(1 for i in issues if i.severity == "error")

        summary_parts = [
            f"Overall quality score: {scores.overall}/10."
        ]

        if critical_issues > 0:
            summary_parts.append(f"Found {critical_issues} critical issue(s) that need immediate attention.")
        if error_issues > 0:
            summary_parts.append(f"Found {error_issues} error(s) that should be fixed.")

        # Highlight strengths
        strengths = []
        if scores.readability >= 8:
            strengths.append("readability")
        if scores.security >= 8:
            strengths.append("security")
        if scores.performance >= 8:
            strengths.append("performance")

        if strengths:
            summary_parts.append(f"Code shows good {', '.join(strengths)}.")

        # Highlight areas for improvement
        weaknesses = []
        if scores.documentation < 5:
            weaknesses.append("documentation")
        if scores.maintainability < 5:
            weaknesses.append("maintainability")

        if weaknesses:
            summary_parts.append(f"Consider improving {', '.join(weaknesses)}.")

        if suggestions:
            summary_parts.append(f"{len(suggestions)} improvement suggestion(s) provided.")

        return " ".join(summary_parts)
