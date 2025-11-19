"""
Service for Plugin management and loading.

Handles plugin registration, loading, and execution.
"""

import importlib.util
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.database import Database
from app.models.plugin import (
    PluginCreate,
    PluginResponse,
    PluginStatus,
    PluginType,
    PluginUpdate,
)
from app.utils.storage import get_storage_service
from app.utils.validators import PluginValidator

logger = logging.getLogger(__name__)

settings = get_settings()


class PluginService:
    """Service for managing plugins."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the plugin service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.plugins
        self._loaded_plugins: Dict[str, Any] = {}

    async def create_plugin(
        self,
        plugin_data: PluginCreate,
        file_content: BinaryIO,
        filename: str,
    ) -> PluginResponse:
        """
        Create a new plugin.

        Args:
            plugin_data: Plugin metadata
            file_content: Plugin file content
            filename: Original filename

        Returns:
            Created plugin response

        Raises:
            ValueError: If validation fails
        """
        # Validate entry point
        is_valid, msg = PluginValidator.validate_entry_point(plugin_data.entry_point)
        if not is_valid:
            raise ValueError(msg)

        # Check if plugin with same name exists
        existing = await self.collection.find_one({"name": plugin_data.name})
        if existing:
            raise ValueError(f"Plugin '{plugin_data.name}' already exists")

        # Validate plugin file
        is_valid, msg, metadata = await PluginValidator.validate_plugin_file(
            file_content, filename
        )
        if not is_valid:
            raise ValueError(msg)

        # Save file to storage
        storage = await get_storage_service()
        file_path, file_size = await storage.save_plugin_file(
            file_content, plugin_data.name
        )

        # Create database document
        now = datetime.utcnow()
        document = {
            "name": plugin_data.name,
            "description": plugin_data.description,
            "plugin_type": plugin_data.plugin_type.value,
            "version": plugin_data.version,
            "author": plugin_data.author,
            "entry_point": plugin_data.entry_point,
            "file_path": file_path,
            "status": PluginStatus.INACTIVE.value,
            "dependencies": plugin_data.dependencies,
            "config": plugin_data.config,
            "config_schema": plugin_data.config_schema,
            "metadata": plugin_data.metadata,
            "error_message": None,
            "load_count": 0,
            "last_loaded_at": None,
            "created_at": now,
            "updated_at": now,
            "created_by": plugin_data.created_by,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = str(result.inserted_id)

        logger.info(f"Plugin created: {plugin_data.name}")
        return self._document_to_response(document)

    async def get_plugin(self, plugin_id: str) -> Optional[PluginResponse]:
        """
        Get a plugin by ID.

        Args:
            plugin_id: Plugin ID

        Returns:
            Plugin response or None if not found
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(plugin_id)})
            if document:
                return self._document_to_response(document)
            return None
        except Exception as e:
            logger.error(f"Error getting plugin {plugin_id}: {e}")
            return None

    async def get_plugin_by_name(self, name: str) -> Optional[PluginResponse]:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin response or None if not found
        """
        document = await self.collection.find_one({"name": name.lower()})
        if document:
            return self._document_to_response(document)
        return None

    async def list_plugins(
        self,
        page: int = 1,
        page_size: int = 20,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None,
        search: Optional[str] = None,
    ) -> dict:
        """
        List plugins with filtering and pagination.

        Args:
            page: Page number
            page_size: Items per page
            plugin_type: Filter by plugin type
            status: Filter by status
            search: Search in name and description

        Returns:
            Dictionary with items, total, page, page_size, pages
        """
        # Build query
        query = {}

        if plugin_type:
            query["plugin_type"] = plugin_type.value

        if status:
            query["status"] = status.value

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]

        # Get total count
        total = await self.collection.count_documents(query)

        # Calculate pagination
        skip = (page - 1) * page_size
        pages = (total + page_size - 1) // page_size

        # Get documents
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        documents = await cursor.to_list(length=page_size)

        items = [self._document_to_response(doc) for doc in documents]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }

    async def update_plugin(
        self, plugin_id: str, update_data: PluginUpdate
    ) -> Optional[PluginResponse]:
        """
        Update a plugin.

        Args:
            plugin_id: Plugin ID
            update_data: Update data

        Returns:
            Updated plugin response or None if not found
        """
        # Build update document
        update_fields = {}

        if update_data.description is not None:
            update_fields["description"] = update_data.description

        if update_data.version is not None:
            update_fields["version"] = update_data.version

        if update_data.config is not None:
            update_fields["config"] = update_data.config

        if update_data.metadata is not None:
            update_fields["metadata"] = update_data.metadata

        if update_data.status is not None:
            update_fields["status"] = update_data.status.value

        if not update_fields:
            return await self.get_plugin(plugin_id)

        update_fields["updated_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(plugin_id)},
            {"$set": update_fields},
            return_document=True,
        )

        if result:
            logger.info(f"Plugin updated: {plugin_id}")
            return self._document_to_response(result)
        return None

    async def delete_plugin(self, plugin_id: str) -> bool:
        """
        Delete a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if deleted, False if not found
        """
        # Get plugin to delete file
        document = await self.collection.find_one({"_id": ObjectId(plugin_id)})
        if document:
            # Unload if loaded
            if plugin_id in self._loaded_plugins:
                await self.unload_plugin(plugin_id)

            # Delete file from storage
            storage = await get_storage_service()
            await storage.delete_file(document["file_path"])

            # Delete from database
            await self.collection.delete_one({"_id": ObjectId(plugin_id)})
            logger.info(f"Plugin deleted: {plugin_id}")
            return True

        return False

    async def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin into memory.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if loaded successfully
        """
        document = await self.collection.find_one({"_id": ObjectId(plugin_id)})
        if not document:
            return False

        try:
            # Update status to loading
            await self.collection.update_one(
                {"_id": ObjectId(plugin_id)},
                {"$set": {"status": PluginStatus.LOADING.value}}
            )

            # Load the plugin module
            file_path = document["file_path"]
            entry_point = document["entry_point"]
            module_name, class_name = entry_point.split(":")

            # Load module dynamically
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load module spec from {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Get the plugin class
            plugin_class = getattr(module, class_name)

            # Instantiate with config
            config = document.get("config", {})
            plugin_instance = plugin_class(config)

            # Store loaded plugin
            self._loaded_plugins[plugin_id] = {
                "instance": plugin_instance,
                "module": module,
                "class_name": class_name,
                "loaded_at": datetime.utcnow(),
            }

            # Update database
            await self.collection.update_one(
                {"_id": ObjectId(plugin_id)},
                {
                    "$set": {
                        "status": PluginStatus.ACTIVE.value,
                        "last_loaded_at": datetime.utcnow(),
                        "error_message": None,
                    },
                    "$inc": {"load_count": 1},
                }
            )

            logger.info(f"Plugin loaded: {document['name']}")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to load plugin {plugin_id}: {error_msg}")

            await self.collection.update_one(
                {"_id": ObjectId(plugin_id)},
                {
                    "$set": {
                        "status": PluginStatus.ERROR.value,
                        "error_message": error_msg,
                    }
                }
            )
            return False

    async def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin from memory.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if unloaded successfully
        """
        if plugin_id not in self._loaded_plugins:
            return False

        try:
            # Update status to unloading
            await self.collection.update_one(
                {"_id": ObjectId(plugin_id)},
                {"$set": {"status": PluginStatus.UNLOADING.value}}
            )

            # Remove from loaded plugins
            plugin_info = self._loaded_plugins.pop(plugin_id)

            # Remove module from sys.modules if present
            module = plugin_info.get("module")
            if module and module.__name__ in sys.modules:
                del sys.modules[module.__name__]

            # Update status
            await self.collection.update_one(
                {"_id": ObjectId(plugin_id)},
                {"$set": {"status": PluginStatus.INACTIVE.value}}
            )

            logger.info(f"Plugin unloaded: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    async def execute_plugin(
        self,
        plugin_id: str,
        input_data: Any,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Execute a loaded plugin.

        Args:
            plugin_id: Plugin ID
            input_data: Input data for the plugin
            config_override: Optional config overrides

        Returns:
            Execution result dictionary
        """
        if plugin_id not in self._loaded_plugins:
            # Try to load the plugin
            loaded = await self.load_plugin(plugin_id)
            if not loaded:
                return {
                    "plugin_id": plugin_id,
                    "success": False,
                    "output_data": None,
                    "execution_time_ms": 0,
                    "error": "Plugin not loaded and failed to load",
                }

        plugin_info = self._loaded_plugins[plugin_id]
        plugin_instance = plugin_info["instance"]

        start_time = time.time()

        try:
            # Apply config override if provided
            if config_override and hasattr(plugin_instance, "configure"):
                plugin_instance.configure(config_override)

            # Execute the plugin
            if hasattr(plugin_instance, "execute"):
                output = plugin_instance.execute(input_data)
            elif hasattr(plugin_instance, "process"):
                output = plugin_instance.process(input_data)
            elif hasattr(plugin_instance, "__call__"):
                output = plugin_instance(input_data)
            else:
                raise AttributeError("Plugin must have execute, process, or __call__ method")

            execution_time_ms = (time.time() - start_time) * 1000

            return {
                "plugin_id": plugin_id,
                "success": True,
                "output_data": output,
                "execution_time_ms": execution_time_ms,
                "error": None,
            }

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            logger.error(f"Plugin execution failed {plugin_id}: {error_msg}")

            return {
                "plugin_id": plugin_id,
                "success": False,
                "output_data": None,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
            }

    async def get_loaded_plugins(self) -> List[str]:
        """
        Get list of currently loaded plugin IDs.

        Returns:
            List of plugin IDs
        """
        return list(self._loaded_plugins.keys())

    async def load_all_active_plugins(self) -> int:
        """
        Load all plugins marked as active.

        Returns:
            Number of plugins loaded
        """
        cursor = self.collection.find({"status": PluginStatus.ACTIVE.value})
        documents = await cursor.to_list(length=1000)

        loaded_count = 0
        for doc in documents:
            plugin_id = str(doc["_id"])
            if await self.load_plugin(plugin_id):
                loaded_count += 1

        logger.info(f"Loaded {loaded_count} active plugins")
        return loaded_count

    def _document_to_response(self, document: dict) -> PluginResponse:
        """Convert MongoDB document to response model."""
        return PluginResponse(
            id=str(document["_id"]),
            name=document["name"],
            description=document.get("description"),
            plugin_type=PluginType(document["plugin_type"]),
            version=document.get("version", "1.0.0"),
            author=document.get("author"),
            entry_point=document["entry_point"],
            file_path=document["file_path"],
            status=PluginStatus(document["status"]),
            dependencies=document.get("dependencies", []),
            config=document.get("config", {}),
            config_schema=document.get("config_schema", {}),
            metadata=document.get("metadata", {}),
            error_message=document.get("error_message"),
            load_count=document.get("load_count", 0),
            last_loaded_at=document.get("last_loaded_at"),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            created_by=document["created_by"],
        )


async def get_plugin_service() -> PluginService:
    """
    FastAPI dependency to get plugin service.

    Returns:
        PluginService instance
    """
    db = Database.get_db()
    return PluginService(db)
