"""
Data transformation utilities for the Data Integration module.

Provides data transformation, validation, and mapping capabilities.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class DataTransformer:
    """
    Transforms and validates data for the Data Integration module.

    Provides utilities for data mapping, validation, filtering,
    and format conversion.
    """

    def __init__(self):
        """Initialize the data transformer."""
        self._transformation_stats = {
            "total_transformations": 0,
            "successful": 0,
            "failed": 0,
        }

    def transform_event_data(
        self, data: Dict[str, Any], schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform event data according to a schema.

        Args:
            data: Input data to transform
            schema: Transformation schema

        Returns:
            Transformed data
        """
        self._transformation_stats["total_transformations"] += 1

        try:
            result = {}

            for target_key, source_config in schema.items():
                if isinstance(source_config, str):
                    # Simple field mapping
                    result[target_key] = self._get_nested_value(data, source_config)
                elif isinstance(source_config, dict):
                    # Complex transformation
                    source_key = source_config.get("source")
                    transform = source_config.get("transform")
                    default = source_config.get("default")

                    value = self._get_nested_value(data, source_key)
                    if value is None:
                        value = default

                    if transform and value is not None:
                        value = self._apply_transform(value, transform)

                    result[target_key] = value

            self._transformation_stats["successful"] += 1
            return result

        except Exception as e:
            logger.error("Transformation failed", error=str(e))
            self._transformation_stats["failed"] += 1
            raise

    def _get_nested_value(
        self, data: Dict[str, Any], path: str
    ) -> Optional[Any]:
        """
        Get a nested value from a dictionary using dot notation.

        Args:
            data: Source dictionary
            path: Dot-separated path (e.g., "user.profile.name")

        Returns:
            Value at the path or None
        """
        if not path:
            return None

        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                value = value[index] if index < len(value) else None
            else:
                return None

        return value

    def _apply_transform(self, value: Any, transform: str) -> Any:
        """
        Apply a transformation to a value.

        Args:
            value: Value to transform
            transform: Transformation name

        Returns:
            Transformed value
        """
        transformations = {
            "lowercase": lambda v: str(v).lower() if v else v,
            "uppercase": lambda v: str(v).upper() if v else v,
            "strip": lambda v: str(v).strip() if v else v,
            "int": lambda v: int(v) if v else 0,
            "float": lambda v: float(v) if v else 0.0,
            "bool": lambda v: bool(v),
            "string": lambda v: str(v) if v else "",
            "list": lambda v: list(v) if v else [],
            "timestamp": lambda v: self._parse_timestamp(v),
            "hash_md5": lambda v: hashlib.md5(str(v).encode()).hexdigest() if v else None,
            "hash_sha256": lambda v: hashlib.sha256(str(v).encode()).hexdigest() if v else None,
        }

        transform_func = transformations.get(transform)
        if transform_func:
            return transform_func(value)

        return value

    def _parse_timestamp(self, value: Any) -> Optional[str]:
        """
        Parse and normalize a timestamp value.

        Args:
            value: Timestamp value (various formats)

        Returns:
            ISO format timestamp string
        """
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt.isoformat()
            except ValueError:
                return value
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
            return dt.isoformat()

        return None

    def filter_data(
        self,
        data: Dict[str, Any],
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Filter dictionary fields.

        Args:
            data: Input dictionary
            include_fields: Fields to include (whitelist)
            exclude_fields: Fields to exclude (blacklist)

        Returns:
            Filtered dictionary
        """
        if include_fields:
            return {k: v for k, v in data.items() if k in include_fields}
        elif exclude_fields:
            return {k: v for k, v in data.items() if k not in exclude_fields}

        return data

    def flatten_dict(
        self, data: Dict[str, Any], separator: str = "."
    ) -> Dict[str, Any]:
        """
        Flatten a nested dictionary.

        Args:
            data: Nested dictionary
            separator: Key separator for flattening

        Returns:
            Flattened dictionary
        """
        result = {}

        def _flatten(obj: Any, prefix: str = "") -> None:
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}{separator}{key}" if prefix else key
                    _flatten(value, new_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{prefix}{separator}{i}" if prefix else str(i)
                    _flatten(item, new_key)
            else:
                result[prefix] = obj

        _flatten(data)
        return result

    def unflatten_dict(
        self, data: Dict[str, Any], separator: str = "."
    ) -> Dict[str, Any]:
        """
        Unflatten a flat dictionary to nested structure.

        Args:
            data: Flat dictionary
            separator: Key separator

        Returns:
            Nested dictionary
        """
        result = {}

        for key, value in data.items():
            keys = key.split(separator)
            current = result

            for i, k in enumerate(keys[:-1]):
                if k not in current:
                    # Check if next key is numeric
                    next_key = keys[i + 1]
                    current[k] = [] if next_key.isdigit() else {}
                current = current[k]

            final_key = keys[-1]
            if isinstance(current, list):
                index = int(final_key)
                while len(current) <= index:
                    current.append(None)
                current[index] = value
            else:
                current[final_key] = value

        return result

    def merge_dicts(
        self, *dicts: Dict[str, Any], deep: bool = True
    ) -> Dict[str, Any]:
        """
        Merge multiple dictionaries.

        Args:
            *dicts: Dictionaries to merge
            deep: Whether to perform deep merge

        Returns:
            Merged dictionary
        """
        result = {}

        for d in dicts:
            if deep:
                result = self._deep_merge(result, d)
            else:
                result.update(d)

        return result

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary with overriding values

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """
        Validate that required fields are present.

        Args:
            data: Dictionary to validate
            required_fields: List of required field names

        Returns:
            List of missing field names
        """
        missing = []

        for field in required_fields:
            value = self._get_nested_value(data, field)
            if value is None:
                missing.append(field)

        return missing

    def sanitize_string(self, value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string value.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]

        return value

    def mask_sensitive_data(
        self, data: Dict[str, Any], sensitive_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Mask sensitive fields in a dictionary.

        Args:
            data: Dictionary with potentially sensitive data
            sensitive_fields: List of field names to mask

        Returns:
            Dictionary with masked sensitive fields
        """
        result = data.copy()

        for field in sensitive_fields:
            if field in result:
                value = result[field]
                if isinstance(value, str) and len(value) > 4:
                    result[field] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                else:
                    result[field] = "***"

        return result

    def extract_patterns(
        self, data: Dict[str, Any], patterns: Dict[str, str]
    ) -> Dict[str, Optional[str]]:
        """
        Extract values using regex patterns.

        Args:
            data: Source data
            patterns: Dict of {result_key: regex_pattern}

        Returns:
            Dict of extracted values
        """
        result = {}

        for key, pattern in patterns.items():
            # Get the source value
            source_value = str(data.get(key, ""))
            match = re.search(pattern, source_value)
            result[key] = match.group(0) if match else None

        return result

    def convert_units(
        self,
        value: Union[int, float],
        from_unit: str,
        to_unit: str,
    ) -> float:
        """
        Convert between common units.

        Args:
            value: Numeric value to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            Converted value
        """
        # Time conversions (to seconds)
        time_to_seconds = {
            "ms": 0.001,
            "s": 1,
            "min": 60,
            "h": 3600,
            "d": 86400,
        }

        # Size conversions (to bytes)
        size_to_bytes = {
            "b": 1,
            "kb": 1024,
            "mb": 1024**2,
            "gb": 1024**3,
            "tb": 1024**4,
        }

        from_unit_lower = from_unit.lower()
        to_unit_lower = to_unit.lower()

        # Check time units
        if from_unit_lower in time_to_seconds and to_unit_lower in time_to_seconds:
            seconds = value * time_to_seconds[from_unit_lower]
            return seconds / time_to_seconds[to_unit_lower]

        # Check size units
        if from_unit_lower in size_to_bytes and to_unit_lower in size_to_bytes:
            bytes_val = value * size_to_bytes[from_unit_lower]
            return bytes_val / size_to_bytes[to_unit_lower]

        raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get transformation statistics.

        Returns:
            Dict containing transformation stats
        """
        return {
            "total_transformations": self._transformation_stats["total_transformations"],
            "successful": self._transformation_stats["successful"],
            "failed": self._transformation_stats["failed"],
            "success_rate": (
                self._transformation_stats["successful"]
                / self._transformation_stats["total_transformations"]
                * 100
                if self._transformation_stats["total_transformations"] > 0
                else 0
            ),
        }
