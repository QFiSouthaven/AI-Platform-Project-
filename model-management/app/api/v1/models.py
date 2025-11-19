"""
API endpoints for AI Model management.

Provides CRUD operations and model loading capabilities.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.models.ai_model import (
    AIModelCreate,
    AIModelList,
    AIModelResponse,
    AIModelUpdate,
    Framework,
    ModelLoadRequest,
    ModelLoadResponse,
    ModelType,
)
from app.services.loader import get_model_loader, ModelLoader
from app.services.model_service import get_model_service, ModelService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=AIModelResponse, status_code=201)
async def create_model(
    file: UploadFile = File(..., description="Model file to upload"),
    name: str = Form(..., description="Model name"),
    version: str = Form(..., description="Model version"),
    model_type: ModelType = Form(..., description="Type of AI model"),
    framework: Framework = Form(..., description="ML framework"),
    description: Optional[str] = Form(None, description="Model description"),
    tags: str = Form("", description="Comma-separated tags"),
    metadata: str = Form("{}", description="JSON metadata"),
    encrypted: bool = Form(False, description="Encrypt model file"),
    created_by: str = Form(..., description="Creator username"),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Create a new AI model.

    Upload a model file and register it in the system.
    """
    import json

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Parse metadata
    try:
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    # Create model data
    model_data = AIModelCreate(
        name=name,
        version=version,
        description=description,
        model_type=model_type,
        framework=framework,
        tags=tag_list,
        metadata=metadata_dict,
        encrypted=encrypted,
        created_by=created_by,
    )

    try:
        result = await model_service.create_model(
            model_data, file.file, file.filename or "model"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create model: {e}")
        raise HTTPException(status_code=500, detail="Failed to create model")


@router.get("", response_model=AIModelList)
async def list_models(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    model_type: Optional[ModelType] = Query(None, description="Filter by model type"),
    framework: Optional[Framework] = Query(None, description="Filter by framework"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    model_service: ModelService = Depends(get_model_service),
):
    """
    List AI models with filtering and pagination.
    """
    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    result = await model_service.list_models(
        page=page,
        page_size=page_size,
        model_type=model_type,
        framework=framework,
        tags=tag_list,
        search=search,
        is_active=is_active,
        created_by=created_by,
    )

    return AIModelList(**result)


@router.get("/search", response_model=List[AIModelResponse])
async def search_models(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Search models by text query.
    """
    return await model_service.search_models(q, limit)


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: str,
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get a model by ID.
    """
    model = await model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/name/{name}/version/{version}", response_model=AIModelResponse)
async def get_model_by_name_version(
    name: str,
    version: str,
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get a model by name and version.
    """
    model = await model_service.get_model_by_name_version(name, version)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.get("/name/{name}/latest", response_model=AIModelResponse)
async def get_latest_model_version(
    name: str,
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get the latest version of a model.
    """
    model = await model_service.get_latest_version(name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.patch("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: str,
    update_data: AIModelUpdate,
    model_service: ModelService = Depends(get_model_service),
):
    """
    Update a model's metadata.
    """
    model = await model_service.update_model(model_id, update_data)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    permanent: bool = Query(False, description="Permanently delete the model"),
    model_service: ModelService = Depends(get_model_service),
):
    """
    Delete a model.

    By default, performs a soft delete (marks as inactive).
    Use permanent=true to permanently delete the model and its file.
    """
    deleted = await model_service.delete_model(model_id, soft_delete=not permanent)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "status": "success",
        "message": f"Model {'permanently deleted' if permanent else 'deactivated'}",
        "model_id": model_id,
    }


@router.get("/{model_id}/download")
async def download_model(
    model_id: str,
    model_service: ModelService = Depends(get_model_service),
):
    """
    Download a model file.
    """
    # Get model to check if it exists
    model = await model_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Get file path (handles decryption)
    file_path = await model_service.get_model_file_path(model_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Model file not found")

    filename = f"{model.name}_{model.version}"
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/{model_id}/load", response_model=ModelLoadResponse)
async def load_model(
    model_id: str,
    request: ModelLoadRequest,
    model_loader: ModelLoader = Depends(get_model_loader),
):
    """
    Load a model into memory for inference.
    """
    result = await model_loader.load_model(
        model_id=model_id,
        device=request.device,
        dtype=request.dtype,
    )

    return ModelLoadResponse(
        model_id=result["model_id"],
        loaded=result["loaded"],
        device=result["device"],
        memory_usage_mb=result["memory_usage_mb"],
        load_time_seconds=result["load_time_seconds"],
    )


@router.post("/{model_id}/unload")
async def unload_model(
    model_id: str,
    model_loader: ModelLoader = Depends(get_model_loader),
):
    """
    Unload a model from memory.
    """
    unloaded = await model_loader.unload_model(model_id)
    if not unloaded:
        raise HTTPException(status_code=404, detail="Model not loaded")

    return {
        "status": "success",
        "message": "Model unloaded",
        "model_id": model_id,
    }


@router.get("/{model_id}/predict")
async def predict(
    model_id: str,
    model_loader: ModelLoader = Depends(get_model_loader),
):
    """
    Get model prediction endpoint info.

    Note: Actual prediction should use POST with proper input data.
    """
    model = await model_loader.get_model(model_id)
    if not model:
        return {
            "status": "not_loaded",
            "message": "Model is not loaded. Use POST /models/{model_id}/load first.",
        }

    return {
        "status": "ready",
        "message": "Model is loaded and ready for predictions",
        "model_id": model_id,
    }


@router.get("/loaded/list")
async def list_loaded_models(
    model_loader: ModelLoader = Depends(get_model_loader),
):
    """
    List all currently loaded models.
    """
    models = await model_loader.get_loaded_models()
    total_memory = await model_loader.get_total_memory_usage()

    return {
        "loaded_models": models,
        "count": len(models),
        "total_memory_mb": total_memory,
    }


@router.post("/loaded/clear")
async def clear_loaded_models(
    model_loader: ModelLoader = Depends(get_model_loader),
):
    """
    Unload all models from memory.
    """
    count = await model_loader.clear_all()
    return {
        "status": "success",
        "message": f"Cleared {count} models from memory",
        "count": count,
    }


@router.get("/tag/{tag}", response_model=List[AIModelResponse])
async def get_models_by_tag(
    tag: str,
    model_service: ModelService = Depends(get_model_service),
):
    """
    Get all models with a specific tag.
    """
    return await model_service.get_models_by_tag(tag)
