"""
Service for Model version management.

Handles version tracking, comparison, and lifecycle management.
"""

import logging
from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.database import Database
from app.models.version import (
    ChangeType,
    ModelVersionCreate,
    ModelVersionResponse,
    ModelVersionUpdate,
    VersionStatus,
)
from app.utils.storage import get_storage_service

logger = logging.getLogger(__name__)

settings = get_settings()


class VersionService:
    """Service for managing model versions."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the version service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.model_versions
        self.models_collection = db.models

    async def create_version(
        self,
        version_data: ModelVersionCreate,
        file_path: str,
        file_size: int,
        checksum: str,
    ) -> ModelVersionResponse:
        """
        Create a new model version.

        Args:
            version_data: Version metadata
            file_path: Path to version file
            file_size: File size in bytes
            checksum: SHA256 checksum

        Returns:
            Created version response

        Raises:
            ValueError: If validation fails
        """
        # Check if model exists
        model = await self.models_collection.find_one(
            {"_id": ObjectId(version_data.model_id)}
        )
        if not model:
            raise ValueError(f"Model '{version_data.model_id}' not found")

        # Check if version already exists for this model
        existing = await self.collection.find_one({
            "model_id": version_data.model_id,
            "version": version_data.version,
        })
        if existing:
            raise ValueError(
                f"Version '{version_data.version}' already exists for model"
            )

        # Check max versions limit
        version_count = await self.collection.count_documents(
            {"model_id": version_data.model_id}
        )
        if version_count >= settings.MAX_VERSIONS_PER_MODEL:
            if settings.AUTO_CLEANUP_OLD_VERSIONS:
                await self._cleanup_old_versions(version_data.model_id)
            else:
                raise ValueError(
                    f"Maximum versions ({settings.MAX_VERSIONS_PER_MODEL}) reached for model"
                )

        # Create database document
        now = datetime.utcnow()
        document = {
            "model_id": version_data.model_id,
            "version": version_data.version,
            "description": version_data.description,
            "change_type": version_data.change_type.value,
            "changelog": version_data.changelog,
            "file_path": file_path,
            "file_size": file_size,
            "checksum": checksum,
            "status": VersionStatus.DRAFT.value,
            "metadata": version_data.metadata,
            "performance_metrics": version_data.performance_metrics,
            "parent_version_id": version_data.parent_version_id,
            "created_at": now,
            "updated_at": now,
            "created_by": version_data.created_by,
            "activated_at": None,
            "deprecated_at": None,
            "download_count": 0,
        }

        result = await self.collection.insert_one(document)
        document["_id"] = str(result.inserted_id)

        logger.info(f"Version created: {version_data.version} for model {version_data.model_id}")
        return self._document_to_response(document)

    async def get_version(self, version_id: str) -> Optional[ModelVersionResponse]:
        """
        Get a version by ID.

        Args:
            version_id: Version ID

        Returns:
            Version response or None if not found
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(version_id)})
            if document:
                return self._document_to_response(document)
            return None
        except Exception as e:
            logger.error(f"Error getting version {version_id}: {e}")
            return None

    async def list_versions(
        self,
        model_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[VersionStatus] = None,
    ) -> dict:
        """
        List versions for a model.

        Args:
            model_id: Parent model ID
            page: Page number
            page_size: Items per page
            status: Filter by status

        Returns:
            Dictionary with items, total, page, page_size, pages
        """
        # Build query
        query = {"model_id": model_id}

        if status:
            query["status"] = status.value

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

    async def update_version(
        self, version_id: str, update_data: ModelVersionUpdate
    ) -> Optional[ModelVersionResponse]:
        """
        Update a version.

        Args:
            version_id: Version ID
            update_data: Update data

        Returns:
            Updated version response or None if not found
        """
        # Build update document
        update_fields = {}

        if update_data.description is not None:
            update_fields["description"] = update_data.description

        if update_data.changelog is not None:
            update_fields["changelog"] = update_data.changelog

        if update_data.metadata is not None:
            update_fields["metadata"] = update_data.metadata

        if update_data.performance_metrics is not None:
            update_fields["performance_metrics"] = update_data.performance_metrics

        if update_data.status is not None:
            update_fields["status"] = update_data.status.value
            if update_data.status == VersionStatus.ACTIVE:
                update_fields["activated_at"] = datetime.utcnow()
            elif update_data.status == VersionStatus.DEPRECATED:
                update_fields["deprecated_at"] = datetime.utcnow()

        if not update_fields:
            return await self.get_version(version_id)

        update_fields["updated_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(version_id)},
            {"$set": update_fields},
            return_document=True,
        )

        if result:
            logger.info(f"Version updated: {version_id}")
            return self._document_to_response(result)
        return None

    async def activate_version(self, version_id: str) -> Optional[ModelVersionResponse]:
        """
        Activate a version (makes it the active version).

        Args:
            version_id: Version ID

        Returns:
            Updated version response or None
        """
        # Get version to find model_id
        version = await self.collection.find_one({"_id": ObjectId(version_id)})
        if not version:
            return None

        model_id = version["model_id"]

        # Deactivate current active version
        await self.collection.update_many(
            {"model_id": model_id, "status": VersionStatus.ACTIVE.value},
            {
                "$set": {
                    "status": VersionStatus.DEPRECATED.value,
                    "deprecated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            }
        )

        # Activate the specified version
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(version_id)},
            {
                "$set": {
                    "status": VersionStatus.ACTIVE.value,
                    "activated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
            return_document=True,
        )

        if result:
            logger.info(f"Version activated: {version_id}")
            return self._document_to_response(result)
        return None

    async def deprecate_version(
        self, version_id: str
    ) -> Optional[ModelVersionResponse]:
        """
        Deprecate a version.

        Args:
            version_id: Version ID

        Returns:
            Updated version response or None
        """
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(version_id)},
            {
                "$set": {
                    "status": VersionStatus.DEPRECATED.value,
                    "deprecated_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
            return_document=True,
        )

        if result:
            logger.info(f"Version deprecated: {version_id}")
            return self._document_to_response(result)
        return None

    async def delete_version(self, version_id: str) -> bool:
        """
        Delete a version.

        Args:
            version_id: Version ID

        Returns:
            True if deleted, False if not found
        """
        # Get version to delete file
        document = await self.collection.find_one({"_id": ObjectId(version_id)})
        if document:
            # Delete file from storage
            storage = await get_storage_service()
            await storage.delete_file(document["file_path"])

            # Delete from database
            await self.collection.delete_one({"_id": ObjectId(version_id)})
            logger.info(f"Version deleted: {version_id}")
            return True

        return False

    async def get_active_version(self, model_id: str) -> Optional[ModelVersionResponse]:
        """
        Get the active version for a model.

        Args:
            model_id: Model ID

        Returns:
            Active version or None
        """
        document = await self.collection.find_one({
            "model_id": model_id,
            "status": VersionStatus.ACTIVE.value,
        })
        if document:
            return self._document_to_response(document)
        return None

    async def compare_versions(
        self, version_id_1: str, version_id_2: str
    ) -> Optional[dict]:
        """
        Compare two versions.

        Args:
            version_id_1: First version ID
            version_id_2: Second version ID

        Returns:
            Comparison result or None
        """
        version_1 = await self.get_version(version_id_1)
        version_2 = await self.get_version(version_id_2)

        if not version_1 or not version_2:
            return None

        # Find differences
        differences = {}

        if version_1.file_size != version_2.file_size:
            differences["file_size"] = {
                "v1": version_1.file_size,
                "v2": version_2.file_size,
            }

        if version_1.checksum != version_2.checksum:
            differences["checksum"] = "Files are different"

        # Compare metrics
        metric_comparison = {}
        all_metrics = set(version_1.performance_metrics.keys()) | set(
            version_2.performance_metrics.keys()
        )

        for metric in all_metrics:
            v1_value = version_1.performance_metrics.get(metric, None)
            v2_value = version_2.performance_metrics.get(metric, None)
            metric_comparison[metric] = {"v1": v1_value, "v2": v2_value}

        return {
            "version_1": version_1,
            "version_2": version_2,
            "differences": differences,
            "metric_comparison": metric_comparison,
        }

    async def get_version_lineage(self, version_id: str) -> dict:
        """
        Get version lineage (ancestry).

        Args:
            version_id: Version ID

        Returns:
            Lineage information
        """
        lineage = []
        current_id = version_id

        while current_id:
            version = await self.collection.find_one({"_id": ObjectId(current_id)})
            if not version:
                break

            lineage.append(self._document_to_response(version))
            current_id = version.get("parent_version_id")

        return {
            "version_id": version_id,
            "lineage": lineage,
            "total_versions": len(lineage),
        }

    async def rollback(
        self, model_id: str, target_version_id: str, reason: Optional[str] = None
    ) -> dict:
        """
        Rollback to a previous version.

        Args:
            model_id: Model ID
            target_version_id: Target version ID
            reason: Reason for rollback

        Returns:
            Rollback result
        """
        # Get current active version
        current_active = await self.get_active_version(model_id)
        if not current_active:
            return {
                "success": False,
                "previous_version_id": None,
                "new_active_version_id": None,
                "message": "No active version found",
            }

        # Get target version
        target = await self.get_version(target_version_id)
        if not target:
            return {
                "success": False,
                "previous_version_id": current_active.id,
                "new_active_version_id": None,
                "message": "Target version not found",
            }

        if target.model_id != model_id:
            return {
                "success": False,
                "previous_version_id": current_active.id,
                "new_active_version_id": None,
                "message": "Target version belongs to different model",
            }

        # Activate target version
        await self.activate_version(target_version_id)

        # Log rollback
        logger.info(
            f"Rollback performed: {model_id} from {current_active.id} to {target_version_id}. "
            f"Reason: {reason or 'Not specified'}"
        )

        return {
            "success": True,
            "previous_version_id": current_active.id,
            "new_active_version_id": target_version_id,
            "message": f"Successfully rolled back to version {target.version}",
        }

    async def increment_download_count(self, version_id: str) -> None:
        """
        Increment download count for a version.

        Args:
            version_id: Version ID
        """
        await self.collection.update_one(
            {"_id": ObjectId(version_id)},
            {"$inc": {"download_count": 1}}
        )

    async def _cleanup_old_versions(self, model_id: str) -> int:
        """
        Clean up old versions, keeping only the most recent N.

        Args:
            model_id: Model ID

        Returns:
            Number of versions deleted
        """
        # Get versions sorted by creation date
        cursor = self.collection.find(
            {"model_id": model_id}
        ).sort("created_at", -1)
        versions = await cursor.to_list(length=1000)

        # Keep only the last N versions
        keep_count = settings.KEEP_LAST_N_VERSIONS
        to_delete = versions[keep_count:]

        deleted_count = 0
        for version in to_delete:
            # Don't delete active versions
            if version["status"] != VersionStatus.ACTIVE.value:
                await self.delete_version(str(version["_id"]))
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old versions for model {model_id}")
        return deleted_count

    def _document_to_response(self, document: dict) -> ModelVersionResponse:
        """Convert MongoDB document to response model."""
        return ModelVersionResponse(
            id=str(document["_id"]),
            model_id=document["model_id"],
            version=document["version"],
            description=document.get("description"),
            change_type=ChangeType(document["change_type"]),
            changelog=document.get("changelog"),
            file_path=document["file_path"],
            file_size=document["file_size"],
            checksum=document["checksum"],
            status=VersionStatus(document["status"]),
            metadata=document.get("metadata", {}),
            performance_metrics=document.get("performance_metrics", {}),
            parent_version_id=document.get("parent_version_id"),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            created_by=document["created_by"],
            activated_at=document.get("activated_at"),
            deprecated_at=document.get("deprecated_at"),
            download_count=document.get("download_count", 0),
        )


async def get_version_service() -> VersionService:
    """
    FastAPI dependency to get version service.

    Returns:
        VersionService instance
    """
    db = Database.get_db()
    return VersionService(db)
