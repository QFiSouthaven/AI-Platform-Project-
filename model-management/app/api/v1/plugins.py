"""
API endpoints for Plugin management.

Provides plugin registration, loading, and execution capabilities.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.models.plugin import (
    PluginCreate,
    PluginExecuteRequest,
    PluginExecuteResponse,
    PluginList,
    PluginResponse,
    PluginStatus,
    PluginType,
    PluginUpdate,
)
from app.services.plugin_service import get_plugin_service, PluginService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=PluginResponse, status_code=201)
async def create_plugin(
    file: UploadFile = File(..., description="Plugin Python file"),
    name: str = Form(..., description="Plugin name"),
    plugin_type: PluginType = Form(..., description="Type of plugin"),
    entry_point: str = Form(..., description="Entry point (module:class)"),
    description: Optional[str] = Form(None, description="Plugin description"),
    version: str = Form("1.0.0", description="Plugin version"),
    author: Optional[str] = Form(None, description="Plugin author"),
    dependencies: str = Form("", description="Comma-separated dependencies"),
    config: str = Form("{}", description="JSON configuration"),
    config_schema: str = Form("{}", description="JSON config schema"),
    metadata: str = Form("{}", description="JSON metadata"),
    created_by: str = Form(..., description="Creator username"),
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Create a new plugin.

    Upload a Python plugin file and register it in the system.
    """
    import json

    # Parse dependencies
    dep_list = [d.strip() for d in dependencies.split(",") if d.strip()]

    # Parse JSON fields
    try:
        config_dict = json.loads(config)
        config_schema_dict = json.loads(config_schema)
        metadata_dict = json.loads(metadata)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Create plugin data
    plugin_data = PluginCreate(
        name=name,
        description=description,
        plugin_type=plugin_type,
        version=version,
        author=author,
        entry_point=entry_point,
        dependencies=dep_list,
        config=config_dict,
        config_schema=config_schema_dict,
        metadata=metadata_dict,
        created_by=created_by,
    )

    try:
        result = await plugin_service.create_plugin(
            plugin_data, file.file, file.filename or "plugin.py"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create plugin: {e}")
        raise HTTPException(status_code=500, detail="Failed to create plugin")


@router.get("", response_model=PluginList)
async def list_plugins(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    plugin_type: Optional[PluginType] = Query(None, description="Filter by plugin type"),
    status: Optional[PluginStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    List plugins with filtering and pagination.
    """
    result = await plugin_service.list_plugins(
        page=page,
        page_size=page_size,
        plugin_type=plugin_type,
        status=status,
        search=search,
    )

    return PluginList(**result)


@router.get("/loaded", response_model=List[str])
async def list_loaded_plugins(
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    List currently loaded plugin IDs.
    """
    return await plugin_service.get_loaded_plugins()


@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Get a plugin by ID.
    """
    plugin = await plugin_service.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.get("/name/{name}", response_model=PluginResponse)
async def get_plugin_by_name(
    name: str,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Get a plugin by name.
    """
    plugin = await plugin_service.get_plugin_by_name(name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.patch("/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: str,
    update_data: PluginUpdate,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Update a plugin's metadata and configuration.
    """
    plugin = await plugin_service.update_plugin(plugin_id, update_data)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.delete("/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Delete a plugin.
    """
    deleted = await plugin_service.delete_plugin(plugin_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return {
        "status": "success",
        "message": "Plugin deleted",
        "plugin_id": plugin_id,
    }


@router.post("/{plugin_id}/load")
async def load_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Load a plugin into memory.
    """
    loaded = await plugin_service.load_plugin(plugin_id)
    if not loaded:
        # Get plugin to check for error message
        plugin = await plugin_service.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")

        error_msg = plugin.error_message or "Failed to load plugin"
        raise HTTPException(status_code=500, detail=error_msg)

    return {
        "status": "success",
        "message": "Plugin loaded",
        "plugin_id": plugin_id,
    }


@router.post("/{plugin_id}/unload")
async def unload_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Unload a plugin from memory.
    """
    unloaded = await plugin_service.unload_plugin(plugin_id)
    if not unloaded:
        raise HTTPException(status_code=404, detail="Plugin not loaded")

    return {
        "status": "success",
        "message": "Plugin unloaded",
        "plugin_id": plugin_id,
    }


@router.post("/{plugin_id}/execute", response_model=PluginExecuteResponse)
async def execute_plugin(
    plugin_id: str,
    request: PluginExecuteRequest,
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Execute a plugin with input data.
    """
    result = await plugin_service.execute_plugin(
        plugin_id=plugin_id,
        input_data=request.input_data,
        config_override=request.config_override,
    )

    return PluginExecuteResponse(
        plugin_id=result["plugin_id"],
        success=result["success"],
        output_data=result["output_data"],
        execution_time_ms=result["execution_time_ms"],
        error=result["error"],
    )


@router.post("/load-all-active")
async def load_all_active_plugins(
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Load all plugins that are marked as active.
    """
    count = await plugin_service.load_all_active_plugins()
    return {
        "status": "success",
        "message": f"Loaded {count} active plugins",
        "count": count,
    }


@router.post("/{plugin_id}/configure")
async def configure_plugin(
    plugin_id: str,
    config: Dict[str, Any],
    plugin_service: PluginService = Depends(get_plugin_service),
):
    """
    Update plugin configuration.
    """
    update_data = PluginUpdate(config=config)
    plugin = await plugin_service.update_plugin(plugin_id, update_data)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    return {
        "status": "success",
        "message": "Plugin configuration updated",
        "plugin_id": plugin_id,
        "config": config,
    }
