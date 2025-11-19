"""
API endpoints for Model Version management.

Provides version tracking, comparison, and lifecycle management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.models.version import (
    ChangeType,
    ModelVersionCreate,
    ModelVersionList,
    ModelVersionResponse,
    ModelVersionUpdate,
    RollbackRequest,
    RollbackResponse,
    VersionComparisonRequest,
    VersionComparisonResponse,
    VersionLineage,
    VersionStatus,
)
from app.services.version_service import get_version_service, VersionService
from app.utils.storage import get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ModelVersionResponse, status_code=201)
async def create_version(
    file: UploadFile = File(..., description="Version model file"),
    model_id: str = Form(..., description="Parent model ID"),
    version: str = Form(..., description="Version string"),
    change_type: ChangeType = Form(..., description="Type of change"),
    description: Optional[str] = Form(None, description="Version description"),
    changelog: Optional[str] = Form(None, description="Detailed changelog"),
    metadata: str = Form("{}", description="JSON metadata"),
    performance_metrics: str = Form("{}", description="JSON performance metrics"),
    parent_version_id: Optional[str] = Form(None, description="Parent version ID"),
    created_by: str = Form(..., description="Creator username"),
    version_service: VersionService = Depends(get_version_service),
):
    """
    Create a new model version.

    Upload a version file and register it for version tracking.
    """
    import json
    from pathlib import Path

    # Parse JSON fields
    try:
        metadata_dict = json.loads(metadata)
        metrics_dict = json.loads(performance_metrics)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Save file to storage
    storage = await get_storage_service()
    extension = Path(file.filename or "model").suffix.lower()

    # Create temporary storage path for version
    import hashlib
    import uuid

    temp_filename = f"version_{uuid.uuid4()}{extension}"
    file_content = await file.read()

    # Calculate checksum
    checksum = hashlib.sha256(file_content).hexdigest()
    file_size = len(file_content)

    # Save to temp location (version service will move it)
    temp_path = await storage.create_temp_file(file_content, extension)

    # Create version data
    version_data = ModelVersionCreate(
        model_id=model_id,
        version=version,
        description=description,
        change_type=change_type,
        changelog=changelog,
        metadata=metadata_dict,
        performance_metrics=metrics_dict,
        parent_version_id=parent_version_id,
        created_by=created_by,
    )

    try:
        result = await version_service.create_version(
            version_data, temp_path, file_size, checksum
        )
        return result
    except ValueError as e:
        # Clean up temp file
        await storage.delete_file(temp_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Clean up temp file
        await storage.delete_file(temp_path)
        logger.error(f"Failed to create version: {e}")
        raise HTTPException(status_code=500, detail="Failed to create version")


@router.get("/model/{model_id}", response_model=ModelVersionList)
async def list_versions(
    model_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[VersionStatus] = Query(None, description="Filter by status"),
    version_service: VersionService = Depends(get_version_service),
):
    """
    List versions for a model.
    """
    result = await version_service.list_versions(
        model_id=model_id,
        page=page,
        page_size=page_size,
        status=status,
    )

    return ModelVersionList(**result)


@router.get("/model/{model_id}/active", response_model=ModelVersionResponse)
async def get_active_version(
    model_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Get the active version for a model.
    """
    version = await version_service.get_active_version(model_id)
    if not version:
        raise HTTPException(status_code=404, detail="No active version found")
    return version


@router.get("/{version_id}", response_model=ModelVersionResponse)
async def get_version(
    version_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Get a version by ID.
    """
    version = await version_service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.patch("/{version_id}", response_model=ModelVersionResponse)
async def update_version(
    version_id: str,
    update_data: ModelVersionUpdate,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Update a version's metadata.
    """
    version = await version_service.update_version(version_id, update_data)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.delete("/{version_id}")
async def delete_version(
    version_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Delete a version.
    """
    deleted = await version_service.delete_version(version_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Version not found")

    return {
        "status": "success",
        "message": "Version deleted",
        "version_id": version_id,
    }


@router.post("/{version_id}/activate", response_model=ModelVersionResponse)
async def activate_version(
    version_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Activate a version (make it the active version).

    This will deactivate the current active version.
    """
    version = await version_service.activate_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/{version_id}/deprecate", response_model=ModelVersionResponse)
async def deprecate_version(
    version_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Deprecate a version.
    """
    version = await version_service.deprecate_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.get("/{version_id}/download")
async def download_version(
    version_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Download a version file.
    """
    version = await version_service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Increment download count
    await version_service.increment_download_count(version_id)

    filename = f"model_{version.model_id}_{version.version}"
    return FileResponse(
        version.file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/compare", response_model=VersionComparisonResponse)
async def compare_versions(
    request: VersionComparisonRequest,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Compare two versions.
    """
    result = await version_service.compare_versions(
        request.version_id_1, request.version_id_2
    )
    if not result:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    return VersionComparisonResponse(
        version_1=result["version_1"],
        version_2=result["version_2"],
        differences=result["differences"],
        metric_comparison=result["metric_comparison"],
    )


@router.get("/{version_id}/lineage", response_model=VersionLineage)
async def get_version_lineage(
    version_id: str,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Get version lineage (ancestry).
    """
    result = await version_service.get_version_lineage(version_id)
    return VersionLineage(**result)


@router.post("/rollback", response_model=RollbackResponse)
async def rollback_version(
    request: RollbackRequest,
    model_id: str = Query(..., description="Model ID"),
    version_service: VersionService = Depends(get_version_service),
):
    """
    Rollback to a previous version.
    """
    result = await version_service.rollback(
        model_id=model_id,
        target_version_id=request.target_version_id,
        reason=request.reason,
    )

    return RollbackResponse(
        success=result["success"],
        previous_version_id=result["previous_version_id"] or "",
        new_active_version_id=result["new_active_version_id"] or "",
        message=result["message"],
    )


@router.post("/{version_id}/metrics")
async def update_performance_metrics(
    version_id: str,
    metrics: dict,
    version_service: VersionService = Depends(get_version_service),
):
    """
    Update performance metrics for a version.
    """
    update_data = ModelVersionUpdate(performance_metrics=metrics)
    version = await version_service.update_version(version_id, update_data)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return {
        "status": "success",
        "message": "Metrics updated",
        "version_id": version_id,
        "metrics": metrics,
    }
