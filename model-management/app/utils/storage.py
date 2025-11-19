"""
File storage service for model and plugin files.

Handles file operations, checksums, and storage management.
Windows compatible implementation using pathlib.Path.
"""

import hashlib
import logging
import os
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

import aiofiles
import aiofiles.os

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def normalize_path(path: str) -> str:
    """Normalize path for cross-platform compatibility."""
    return str(Path(path).resolve())


class StorageService:
    """Service for managing file storage operations."""

    def __init__(self):
        """Initialize the storage service."""
        self.model_path = Path(settings.MODEL_STORAGE_PATH)
        self.plugin_path = Path(settings.PLUGIN_STORAGE_PATH)
        self.temp_path = Path(settings.TEMP_STORAGE_PATH)

    async def initialize(self) -> None:
        """Initialize storage directories."""
        for path in [self.model_path, self.plugin_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
        logger.info("Storage service initialized")

    async def save_model_file(
        self,
        file_content: BinaryIO,
        model_name: str,
        version: str,
        extension: str,
    ) -> Tuple[str, int, str]:
        """
        Save a model file to storage.

        Args:
            file_content: File content to save
            model_name: Name of the model
            version: Model version
            extension: File extension

        Returns:
            Tuple of (file_path, file_size, checksum)
        """
        # Create directory structure: models/{model_name}/{version}/
        model_dir = self.model_path / model_name / version
        model_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        filename = f"{model_name}_{version}_{file_id}{extension}"
        file_path = model_dir / filename

        # Calculate checksum while saving
        sha256_hash = hashlib.sha256()
        file_size = 0

        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = file_content.read(8192)
                if not chunk:
                    break
                await f.write(chunk)
                sha256_hash.update(chunk)
                file_size += len(chunk)

        checksum = sha256_hash.hexdigest()

        logger.info(f"Model file saved: {file_path} ({file_size} bytes)")
        return str(file_path), file_size, checksum

    async def save_plugin_file(
        self,
        file_content: BinaryIO,
        plugin_name: str,
        extension: str = ".py",
    ) -> Tuple[str, int]:
        """
        Save a plugin file to storage.

        Args:
            file_content: File content to save
            plugin_name: Name of the plugin
            extension: File extension

        Returns:
            Tuple of (file_path, file_size)
        """
        # Create directory structure: plugins/{plugin_name}/
        plugin_dir = self.plugin_path / plugin_name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{plugin_name}{extension}"
        file_path = plugin_dir / filename

        file_size = 0
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = file_content.read(8192)
                if not chunk:
                    break
                await f.write(chunk)
                file_size += len(chunk)

        logger.info(f"Plugin file saved: {file_path} ({file_size} bytes)")
        return str(file_path), file_size

    async def get_file(self, file_path: str) -> bytes:
        """
        Read a file from storage.

        Args:
            file_path: Path to file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()

        return content

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to file

        Returns:
            True if deleted, False if not found
        """
        try:
            if os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
                logger.info(f"File deleted: {file_path}")

                # Clean up empty parent directories
                parent = Path(file_path).parent
                await self._cleanup_empty_dirs(parent)

                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise

    async def _cleanup_empty_dirs(self, directory: Path) -> None:
        """Remove empty parent directories up to storage root."""
        storage_roots = [self.model_path, self.plugin_path]

        while directory not in storage_roots:
            try:
                if directory.exists() and not any(directory.iterdir()):
                    directory.rmdir()
                    directory = directory.parent
                else:
                    break
            except Exception:
                break

    async def copy_file(self, source: str, destination: str) -> str:
        """
        Copy a file within storage.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Destination path
        """
        dest_dir = Path(destination).parent
        dest_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, destination)
        logger.info(f"File copied: {source} -> {destination}")
        return destination

    async def move_file(self, source: str, destination: str) -> str:
        """
        Move a file within storage.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            Destination path
        """
        dest_dir = Path(destination).parent
        dest_dir.mkdir(parents=True, exist_ok=True)

        shutil.move(source, destination)
        logger.info(f"File moved: {source} -> {destination}")

        # Clean up empty source directories
        await self._cleanup_empty_dirs(Path(source).parent)

        return destination

    async def calculate_checksum(self, file_path: str) -> str:
        """
        Calculate SHA256 checksum of a file.

        Args:
            file_path: Path to file

        Returns:
            Hex-encoded checksum
        """
        sha256_hash = hashlib.sha256()

        async with aiofiles.open(file_path, "rb") as f:
            while True:
                chunk = await f.read(8192)
                if not chunk:
                    break
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    async def verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """
        Verify file checksum.

        Args:
            file_path: Path to file
            expected_checksum: Expected checksum

        Returns:
            True if checksum matches
        """
        actual_checksum = await self.calculate_checksum(file_path)
        return actual_checksum == expected_checksum

    async def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes
        """
        stat = await aiofiles.os.stat(file_path)
        return stat.st_size

    async def get_file_info(self, file_path: str) -> dict:
        """
        Get detailed file information.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = await aiofiles.os.stat(file_path)

        return {
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "checksum": await self.calculate_checksum(file_path),
        }

    async def list_model_files(self, model_name: Optional[str] = None) -> list:
        """
        List model files in storage.

        Args:
            model_name: Optional filter by model name

        Returns:
            List of file paths (normalized for platform)
        """
        if model_name:
            search_path = self.model_path / model_name
        else:
            search_path = self.model_path

        if not search_path.exists():
            return []

        files = []
        for root, _, filenames in os.walk(search_path):
            for filename in filenames:
                # Use Path for cross-platform path handling
                file_path = Path(root) / filename
                files.append(str(file_path))

        return files

    async def get_storage_stats(self) -> dict:
        """
        Get storage usage statistics.

        Returns:
            Dictionary with storage statistics
        """
        model_size = await self._get_dir_size(self.model_path)
        plugin_size = await self._get_dir_size(self.plugin_path)
        temp_size = await self._get_dir_size(self.temp_path)

        # Get disk usage
        disk_usage = shutil.disk_usage(self.model_path)

        return {
            "model_storage_bytes": model_size,
            "plugin_storage_bytes": plugin_size,
            "temp_storage_bytes": temp_size,
            "total_used_bytes": model_size + plugin_size + temp_size,
            "disk_total_bytes": disk_usage.total,
            "disk_used_bytes": disk_usage.used,
            "disk_free_bytes": disk_usage.free,
        }

    async def _get_dir_size(self, path: Path) -> int:
        """Calculate total size of directory."""
        total_size = 0
        if path.exists():
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    # Use Path for cross-platform compatibility
                    filepath = Path(dirpath) / filename
                    try:
                        total_size += filepath.stat().st_size
                    except (OSError, IOError):
                        # Skip files that can't be accessed
                        pass
        return total_size

    async def create_temp_file(self, content: bytes, extension: str = "") -> str:
        """
        Create a temporary file.

        Args:
            content: File content
            extension: File extension

        Returns:
            Path to temporary file
        """
        filename = f"{uuid.uuid4()}{extension}"
        file_path = self.temp_path / filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return str(file_path)

    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        if self.temp_path.exists():
            for file_path in self.temp_path.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    if stat.st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} temporary files")
        return deleted_count


# Global instance
storage_service = StorageService()


async def get_storage_service() -> StorageService:
    """
    FastAPI dependency to get storage service.

    Returns:
        StorageService instance
    """
    return storage_service
