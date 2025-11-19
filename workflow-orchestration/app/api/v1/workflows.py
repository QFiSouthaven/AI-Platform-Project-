"""
Workflow API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workflow import WorkflowStatus, ExecutionStatus
from app.models.schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowListResponse,
    WorkflowExecutionCreate,
    WorkflowExecutionResponse,
    PaginationParams,
    PaginatedResponse,
    APIResponse,
    RequirementAnalysisRequest,
    RequirementAnalysisResponse,
    WorkflowStatistics,
)
from app.services.workflow_service import WorkflowService
from app.services.orchestrator import WorkflowOrchestrator
from app.services.analyzer import RequirementAnalyzer
from app.kafka.producer import get_kafka_producer, KafkaProducer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=APIResponse)
async def create_workflow(
    workflow_data: WorkflowCreate,
    created_by: str = Query(..., description="User creating the workflow"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new workflow.

    - **name**: Workflow name
    - **description**: Optional description
    - **tasks**: List of tasks to create with the workflow
    """
    service = WorkflowService(db)

    try:
        workflow = await service.create_workflow(workflow_data, created_by)
        return APIResponse(
            status="success",
            data=WorkflowResponse.model_validate(workflow),
            message=f"Workflow '{workflow.name}' created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=PaginatedResponse)
async def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[WorkflowStatus] = None,
    created_by: Optional[str] = None,
    is_template: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List workflows with filtering and pagination.
    """
    service = WorkflowService(db)
    pagination = PaginationParams(page=page, page_size=page_size)

    workflows, total = await service.list_workflows(
        pagination,
        status=status,
        created_by=created_by,
        is_template=is_template,
        search=search
    )

    # Convert to list response format
    items = []
    for workflow in workflows:
        items.append(WorkflowListResponse(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status,
            version=workflow.version,
            is_template=workflow.is_template,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            created_by=workflow.created_by,
            tags=workflow.tags,
            task_count=len(workflow.tasks)
        ))

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/statistics", response_model=APIResponse)
async def get_workflow_statistics(
    created_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get workflow statistics.
    """
    service = WorkflowService(db)
    stats = await service.get_workflow_statistics(created_by)

    return APIResponse(
        status="success",
        data=WorkflowStatistics(**stats)
    )


@router.get("/{workflow_id}", response_model=APIResponse)
async def get_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a workflow by ID.
    """
    service = WorkflowService(db)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return APIResponse(
        status="success",
        data=WorkflowResponse.model_validate(workflow)
    )


@router.put("/{workflow_id}", response_model=APIResponse)
async def update_workflow(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a workflow.
    """
    service = WorkflowService(db)
    workflow = await service.update_workflow(workflow_id, workflow_data)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return APIResponse(
        status="success",
        data=WorkflowResponse.model_validate(workflow),
        message="Workflow updated successfully"
    )


@router.delete("/{workflow_id}", response_model=APIResponse)
async def delete_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a workflow.
    """
    service = WorkflowService(db)
    deleted = await service.delete_workflow(workflow_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return APIResponse(
        status="success",
        message=f"Workflow {workflow_id} deleted successfully"
    )


@router.post("/{workflow_id}/activate", response_model=APIResponse)
async def activate_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a draft workflow.
    """
    service = WorkflowService(db)

    try:
        workflow = await service.activate_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return APIResponse(
            status="success",
            data=WorkflowResponse.model_validate(workflow),
            message="Workflow activated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/clone", response_model=APIResponse)
async def clone_workflow(
    workflow_id: int,
    new_name: str = Query(..., min_length=1, max_length=255),
    created_by: str = Query(..., description="User creating the clone"),
    db: AsyncSession = Depends(get_db)
):
    """
    Clone a workflow.
    """
    service = WorkflowService(db)
    workflow = await service.clone_workflow(workflow_id, new_name, created_by)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return APIResponse(
        status="success",
        data=WorkflowResponse.model_validate(workflow),
        message=f"Workflow cloned as '{new_name}'"
    )


@router.post("/{workflow_id}/execute", response_model=APIResponse)
async def execute_workflow(
    workflow_id: int,
    execution_data: WorkflowExecutionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    kafka_producer: KafkaProducer = Depends(get_kafka_producer)
):
    """
    Trigger a workflow execution.
    """
    service = WorkflowService(db)

    try:
        execution = await service.create_execution(workflow_id, execution_data)

        if not execution:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Start execution in background
        orchestrator = WorkflowOrchestrator(db, kafka_producer)
        background_tasks.add_task(
            orchestrator.start_execution,
            workflow_id,
            execution.id
        )

        return APIResponse(
            status="success",
            data=WorkflowExecutionResponse.model_validate(execution),
            message="Workflow execution started"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}/executions", response_model=PaginatedResponse)
async def list_workflow_executions(
    workflow_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[ExecutionStatus] = None,
    triggered_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List executions for a specific workflow.
    """
    service = WorkflowService(db)
    pagination = PaginationParams(page=page, page_size=page_size)

    executions, total = await service.list_executions(
        workflow_id,
        pagination,
        status=status,
        triggered_by=triggered_by
    )

    items = [
        WorkflowExecutionResponse.model_validate(exec)
        for exec in executions
    ]

    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/analyze", response_model=APIResponse)
async def analyze_requirements(
    request: RequirementAnalysisRequest
):
    """
    Analyze requirements and suggest workflow structure.
    """
    analyzer = RequirementAnalyzer()
    result = await analyzer.analyze_requirements(
        request.requirements,
        request.context
    )

    return APIResponse(
        status="success",
        data=RequirementAnalysisResponse(**result),
        message="Requirements analyzed successfully"
    )
