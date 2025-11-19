"""
Service for AI Model CRUD operations.

Handles model creation, retrieval, update, and deletion.
"""

import logging
from datetime import datetime
from typing import BinaryIO, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.database import Database
from app.models.ai_model import (
    AIModelCreate,
    AIModelResponse,
    AIModelUpdate,
    ModelType,
    Framework,
)
from app.utils.encryption import get_encryption_service
from app.utils.storage import get_storage_service
from app.utils.validators import ModelValidator

logger = logging.getLogger(__name__)

settings = get_settings()


class ModelService:
    """Service for managing AI models."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the model service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.models

    async def create_model(
        self,
        model_data: AIModelCreate,
        file_content: BinaryIO,
        filename: str,
    ) -> AIModelResponse:
        """
        Create a new AI model.

        Args:
            model_data: Model metadata
            file_content: Model file content
            filename: Original filename

        Returns:
            Created model response

        Raises:
            ValueError: If validation fails
        """
        # Validate model name
        is_valid, msg = ModelValidator.validate_model_name(model_data.name)
        if not is_valid:
            raise ValueError(msg)

        # Validate version
        is_valid, msg = ModelValidator.validate_version(model_data.version)
        if not is_valid:
            raise ValueError(msg)

        # Check if model with same name and version exists
        existing = await self.collection.find_one({
            "name": model_data.name,
            "version": model_data.version,
        })
        if existing:
            raise ValueError(f"Model '{model_data.name}' version '{model_data.version}' already exists")

        # Validate model file
        is_valid, msg, metadata = await ModelValidator.validate_model_file(
            file_content, filename, model_data.framework.value
        )
        if not is_valid:
            raise ValueError(msg)

        # Get file extension
        from pathlib import Path
        extension = Path(filename).suffix.lower()

        # Save file to storage
        storage = await get_storage_service()
        file_path, file_size, checksum = await storage.save_model_file(
            file_content, model_data.name, model_data.version, extension
        )

        # Encrypt if requested
        if model_data.encrypted and settings.ENABLE_ENCRYPTION:
            encryption = await get_encryption_service()
            encrypted_path = await encryption.encrypt_file(file_path)
            # Remove original unencrypted file
            await storage.delete_file(file_path)
            file_path = encrypted_path

        # Create database document
        now = datetime.utcnow()
        document = {
            "name": model_data.name,
            "version": model_data.version,
            "description": model_data.description,
            "model_type": model_data.model_type.value,
            "framework": model_data.framework.value,
            "file_path": file_path,
            "file_size": file_size,
            "checksum": checksum,
            "encrypted": model_data.encrypted,
            "metadata": model_data.metadata,
            "tags": model_data.tags,
            "created_at": now,
            "updated_at": now,
            "created_by": model_data.created_by,
            "is_active": True,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = str(result.inserted_id)

        logger.info(f"Model created: {model_data.name} v{model_data.version}")
        return self._document_to_response(document)

    async def get_model(self, model_id: str) -> Optional[AIModelResponse]:
        """
        Get a model by ID.

        Args:
            model_id: Model ID

        Returns:
            Model response or None if not found
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(model_id)})
            if document:
                return self._document_to_response(document)
            return None
        except Exception as e:
            logger.error(f"Error getting model {model_id}: {e}")
            return None

    async def get_model_by_name_version(
        self, name: str, version: str
    ) -> Optional[AIModelResponse]:
        """
        Get a model by name and version.

        Args:
            name: Model name
            version: Model version

        Returns:
            Model response or None if not found
        """
        document = await self.collection.find_one({
            "name": name.lower(),
            "version": version,
        })
        if document:
            return self._document_to_response(document)
        return None

    async def list_models(
        self,
        page: int = 1,
        page_size: int = 20,
        model_type: Optional[ModelType] = None,
        framework: Optional[Framework] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_by: Optional[str] = None,
    ) -> dict:
        """
        List models with filtering and pagination.

        Args:
            page: Page number
            page_size: Items per page
            model_type: Filter by model type
            framework: Filter by framework
            tags: Filter by tags
            search: Search in name and description
            is_active: Filter by active status
            created_by: Filter by creator

        Returns:
            Dictionary with items, total, page, page_size, pages
        """
        # Build query
        query = {}

        if model_type:
            query["model_type"] = model_type.value

        if framework:
            query["framework"] = framework.value

        if tags:
            query["tags"] = {"$all": [tag.lower() for tag in tags]}

        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]

        if is_active is not None:
            query["is_active"] = is_active

        if created_by:
            query["created_by"] = created_by

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

    async def update_model(
        self, model_id: str, update_data: AIModelUpdate
    ) -> Optional[AIModelResponse]:
        """
        Update a model.

        Args:
            model_id: Model ID
            update_data: Update data

        Returns:
            Updated model response or None if not found
        """
        # Build update document
        update_fields = {}

        if update_data.description is not None:
            update_fields["description"] = update_data.description

        if update_data.metadata is not None:
            update_fields["metadata"] = update_data.metadata

        if update_data.tags is not None:
            update_fields["tags"] = update_data.tags

        if update_data.is_active is not None:
            update_fields["is_active"] = update_data.is_active

        if not update_fields:
            return await self.get_model(model_id)

        update_fields["updated_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(model_id)},
            {"$set": update_fields},
            return_document=True,
        )

        if result:
            logger.info(f"Model updated: {model_id}")
            return self._document_to_response(result)
        return None

    async def delete_model(self, model_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a model.

        Args:
            model_id: Model ID
            soft_delete: If True, mark as inactive; if False, permanently delete

        Returns:
            True if deleted, False if not found
        """
        if soft_delete:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(model_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
            )
            if result:
                logger.info(f"Model soft deleted: {model_id}")
                return True
        else:
            # Get model to delete file
            document = await self.collection.find_one({"_id": ObjectId(model_id)})
            if document:
                # Delete file from storage
                storage = await get_storage_service()
                await storage.delete_file(document["file_path"])

                # Delete from database
                await self.collection.delete_one({"_id": ObjectId(model_id)})
                logger.info(f"Model permanently deleted: {model_id}")
                return True

        return False

    async def get_model_file_path(self, model_id: str) -> Optional[str]:
        """
        Get the file path for a model.

        Args:
            model_id: Model ID

        Returns:
            File path or None if not found
        """
        document = await self.collection.find_one(
            {"_id": ObjectId(model_id)},
            {"file_path": 1, "encrypted": 1}
        )

        if not document:
            return None

        file_path = document["file_path"]

        # Decrypt if needed
        if document.get("encrypted"):
            encryption = await get_encryption_service()
            storage = await get_storage_service()

            # Create temp decrypted file
            decrypted_path = file_path.replace(".encrypted", "")
            await encryption.decrypt_file(file_path, decrypted_path)
            return decrypted_path

        return file_path

    async def get_models_by_tag(self, tag: str) -> List[AIModelResponse]:
        """
        Get all models with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of model responses
        """
        cursor = self.collection.find({"tags": tag.lower(), "is_active": True})
        documents = await cursor.to_list(length=1000)
        return [self._document_to_response(doc) for doc in documents]

    async def get_latest_version(self, model_name: str) -> Optional[AIModelResponse]:
        """
        Get the latest version of a model.

        Args:
            model_name: Model name

        Returns:
            Latest model version or None
        """
        cursor = self.collection.find(
            {"name": model_name.lower(), "is_active": True}
        ).sort("created_at", -1).limit(1)

        documents = await cursor.to_list(length=1)
        if documents:
            return self._document_to_response(documents[0])
        return None

    async def search_models(
        self, query: str, limit: int = 10
    ) -> List[AIModelResponse]:
        """
        Search models by text query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching models
        """
        search_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}},
            ],
            "is_active": True,
        }

        cursor = self.collection.find(search_query).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [self._document_to_response(doc) for doc in documents]

    def _document_to_response(self, document: dict) -> AIModelResponse:
        """Convert MongoDB document to response model."""
        return AIModelResponse(
            id=str(document["_id"]),
            name=document["name"],
            version=document["version"],
            description=document.get("description"),
            model_type=ModelType(document["model_type"]),
            framework=Framework(document["framework"]),
            file_path=document["file_path"],
            file_size=document["file_size"],
            checksum=document["checksum"],
            encrypted=document.get("encrypted", False),
            metadata=document.get("metadata", {}),
            tags=document.get("tags", []),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            created_by=document["created_by"],
            is_active=document.get("is_active", True),
        )


async def get_model_service() -> ModelService:
    """
    FastAPI dependency to get model service.

    Returns:
        ModelService instance
    """
    db = Database.get_db()
    return ModelService(db)
