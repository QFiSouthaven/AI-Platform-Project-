"""
Validators for model files and data.

Provides validation utilities for model uploads and operations.
"""

import logging
import os
import struct
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ModelValidator:
    """Validator for AI model files."""

    # File signatures for different model formats
    FILE_SIGNATURES = {
        ".pt": [b"\x80\x02", b"PK"],  # PyTorch (pickle or zip)
        ".pth": [b"\x80\x02", b"PK"],  # PyTorch state dict
        ".h5": [b"\x89HDF"],  # HDF5 (Keras/TensorFlow)
        ".onnx": [b"\x08"],  # ONNX protobuf
        ".bin": [b""],  # Binary (various)
        ".safetensors": [b""],  # Safetensors
        ".pkl": [b"\x80\x02", b"\x80\x03", b"\x80\x04", b"\x80\x05"],  # Pickle
    }

    @classmethod
    async def validate_model_file(
        cls,
        file_content: BinaryIO,
        filename: str,
        expected_framework: Optional[str] = None,
    ) -> Tuple[bool, str, dict]:
        """
        Validate a model file.

        Args:
            file_content: File content to validate
            filename: Original filename
            expected_framework: Expected ML framework

        Returns:
            Tuple of (is_valid, message, metadata)
        """
        metadata = {}

        # Check file extension
        extension = Path(filename).suffix.lower()
        if extension not in settings.ALLOWED_MODEL_EXTENSIONS:
            return (
                False,
                f"Invalid file extension: {extension}. Allowed: {settings.ALLOWED_MODEL_EXTENSIONS}",
                metadata,
            )

        # Check file size
        file_content.seek(0, 2)  # Seek to end
        file_size = file_content.tell()
        file_content.seek(0)  # Reset to beginning

        max_size = settings.MAX_MODEL_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            return (
                False,
                f"File too large: {file_size / (1024*1024):.2f}MB. Maximum: {settings.MAX_MODEL_SIZE_MB}MB",
                metadata,
            )

        if file_size == 0:
            return False, "File is empty", metadata

        metadata["file_size"] = file_size
        metadata["extension"] = extension

        # Validate file signature
        header = file_content.read(256)
        file_content.seek(0)

        if extension in cls.FILE_SIGNATURES:
            signatures = cls.FILE_SIGNATURES[extension]
            if signatures and not any(header.startswith(sig) for sig in signatures if sig):
                logger.warning(f"File signature mismatch for {filename}")
                # Don't fail, just warn - some valid files may have different signatures

        # Framework-specific validation
        if expected_framework:
            is_valid, msg = await cls._validate_framework(
                file_content, extension, expected_framework
            )
            if not is_valid:
                return False, msg, metadata

        # Additional checks based on extension
        if extension in [".pt", ".pth"]:
            metadata["format"] = "pytorch"
        elif extension == ".h5":
            metadata["format"] = "hdf5"
        elif extension == ".onnx":
            metadata["format"] = "onnx"
            # Try to extract ONNX metadata
            onnx_meta = cls._extract_onnx_metadata(header)
            if onnx_meta:
                metadata.update(onnx_meta)
        elif extension == ".safetensors":
            metadata["format"] = "safetensors"

        return True, "Validation successful", metadata

    @classmethod
    async def _validate_framework(
        cls,
        file_content: BinaryIO,
        extension: str,
        framework: str,
    ) -> Tuple[bool, str]:
        """
        Validate file matches expected framework.

        Args:
            file_content: File content
            extension: File extension
            framework: Expected framework

        Returns:
            Tuple of (is_valid, message)
        """
        framework = framework.lower()

        # Map frameworks to expected extensions
        framework_extensions = {
            "pytorch": [".pt", ".pth", ".bin"],
            "tensorflow": [".h5", ".pb", ".savedmodel"],
            "keras": [".h5", ".keras"],
            "onnx": [".onnx"],
            "sklearn": [".pkl", ".joblib"],
            "huggingface": [".bin", ".safetensors", ".pt"],
        }

        if framework in framework_extensions:
            if extension not in framework_extensions[framework]:
                return (
                    False,
                    f"Extension {extension} not typical for {framework}. Expected: {framework_extensions[framework]}",
                )

        return True, "Framework validation passed"

    @classmethod
    def _extract_onnx_metadata(cls, header: bytes) -> Optional[dict]:
        """
        Extract metadata from ONNX file header.

        Args:
            header: File header bytes

        Returns:
            Dictionary with ONNX metadata or None
        """
        try:
            # ONNX uses protobuf format
            # This is a simplified extraction
            return {"onnx_version": "detected"}
        except Exception:
            return None

    @classmethod
    def validate_model_name(cls, name: str) -> Tuple[bool, str]:
        """
        Validate model name format.

        Args:
            name: Model name to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not name:
            return False, "Model name cannot be empty"

        if len(name) > 255:
            return False, "Model name too long (max 255 characters)"

        if not name.replace("-", "").replace("_", "").isalnum():
            return (
                False,
                "Model name must contain only alphanumeric characters, hyphens, and underscores",
            )

        # Check for reserved names
        reserved_names = ["system", "admin", "config", "temp", "test"]
        if name.lower() in reserved_names:
            return False, f"Model name '{name}' is reserved"

        return True, "Valid model name"

    @classmethod
    def validate_version(cls, version: str) -> Tuple[bool, str]:
        """
        Validate version string format.

        Args:
            version: Version string to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not version:
            return False, "Version cannot be empty"

        if len(version) > 50:
            return False, "Version string too long (max 50 characters)"

        # Allow semantic versioning and simple versions
        # Examples: 1.0.0, v1.0, 2023.01.15, latest

        return True, "Valid version"

    @classmethod
    def validate_tags(cls, tags: List[str]) -> Tuple[bool, str]:
        """
        Validate tags list.

        Args:
            tags: List of tags to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if len(tags) > 50:
            return False, "Too many tags (max 50)"

        for tag in tags:
            if len(tag) > 100:
                return False, f"Tag too long: {tag[:20]}... (max 100 characters)"

            if not tag.replace("-", "").replace("_", "").replace(" ", "").isalnum():
                return False, f"Invalid tag format: {tag}"

        return True, "Valid tags"

    @classmethod
    async def validate_checksum(
        cls,
        file_content: BinaryIO,
        expected_checksum: str,
    ) -> Tuple[bool, str]:
        """
        Validate file checksum.

        Args:
            file_content: File content
            expected_checksum: Expected SHA256 checksum

        Returns:
            Tuple of (is_valid, message)
        """
        import hashlib

        sha256_hash = hashlib.sha256()

        while True:
            chunk = file_content.read(8192)
            if not chunk:
                break
            sha256_hash.update(chunk)

        file_content.seek(0)
        actual_checksum = sha256_hash.hexdigest()

        if actual_checksum != expected_checksum:
            return (
                False,
                f"Checksum mismatch. Expected: {expected_checksum}, Got: {actual_checksum}",
            )

        return True, "Checksum verified"


class PluginValidator:
    """Validator for plugin files."""

    @classmethod
    async def validate_plugin_file(
        cls,
        file_content: BinaryIO,
        filename: str,
    ) -> Tuple[bool, str, dict]:
        """
        Validate a plugin file.

        Args:
            file_content: File content to validate
            filename: Original filename

        Returns:
            Tuple of (is_valid, message, metadata)
        """
        metadata = {}

        # Check file extension
        extension = Path(filename).suffix.lower()
        if extension != ".py":
            return False, f"Invalid plugin extension: {extension}. Must be .py", metadata

        # Check file size
        file_content.seek(0, 2)
        file_size = file_content.tell()
        file_content.seek(0)

        max_size = 10 * 1024 * 1024  # 10MB max for plugins
        if file_size > max_size:
            return (
                False,
                f"Plugin file too large: {file_size / 1024:.2f}KB. Maximum: 10MB",
                metadata,
            )

        metadata["file_size"] = file_size

        # Read content and validate Python syntax
        content = file_content.read().decode("utf-8")
        file_content.seek(0)

        try:
            compile(content, filename, "exec")
        except SyntaxError as e:
            return False, f"Python syntax error: {e}", metadata

        # Check for required plugin interface
        if "class" not in content:
            return False, "Plugin must contain at least one class definition", metadata

        metadata["has_class"] = True

        return True, "Plugin validation successful", metadata

    @classmethod
    def validate_entry_point(cls, entry_point: str) -> Tuple[bool, str]:
        """
        Validate plugin entry point format.

        Args:
            entry_point: Entry point string (module:class)

        Returns:
            Tuple of (is_valid, message)
        """
        if ":" not in entry_point:
            return False, "Entry point must be in format 'module:class'"

        parts = entry_point.split(":")
        if len(parts) != 2:
            return False, "Entry point must have exactly one colon separator"

        module_name, class_name = parts

        if not module_name:
            return False, "Module name cannot be empty"

        if not class_name:
            return False, "Class name cannot be empty"

        # Validate module name format
        if not all(
            part.isidentifier() for part in module_name.split(".")
        ):
            return False, f"Invalid module name: {module_name}"

        # Validate class name format
        if not class_name.isidentifier():
            return False, f"Invalid class name: {class_name}"

        return True, "Valid entry point"
