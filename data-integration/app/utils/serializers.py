"""
JSON serialization utilities for the Data Integration module.

Provides custom serializers and deserializers for common types.
"""

import json
from datetime import datetime, date, time, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles common Python types.

    Supports UUID, datetime, date, time, Decimal, Enum, and Pydantic models.
    """

    def default(self, obj: Any) -> Any:
        """
        Encode non-standard types.

        Args:
            obj: Object to encode

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, datetime):
            return obj.isoformat()

        if isinstance(obj, date):
            return obj.isoformat()

        if isinstance(obj, time):
            return obj.isoformat()

        if isinstance(obj, Decimal):
            return float(obj)

        if isinstance(obj, Enum):
            return obj.value

        if isinstance(obj, bytes):
            return obj.decode("utf-8")

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, frozenset):
            return list(obj)

        # Handle Pydantic models
        if hasattr(obj, "model_dump"):
            return obj.model_dump()

        # Handle dataclasses
        if hasattr(obj, "__dataclass_fields__"):
            from dataclasses import asdict
            return asdict(obj)

        return super().default(obj)


def serialize_to_json(
    data: Any,
    indent: Optional[int] = None,
    sort_keys: bool = False,
    ensure_ascii: bool = False,
) -> str:
    """
    Serialize Python object to JSON string.

    Args:
        data: Object to serialize
        indent: Indentation level for pretty printing
        sort_keys: Whether to sort dictionary keys
        ensure_ascii: Whether to escape non-ASCII characters

    Returns:
        JSON string
    """
    return json.dumps(
        data,
        cls=CustomJSONEncoder,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
    )


def deserialize_from_json(
    json_string: str,
    strict: bool = False,
) -> Any:
    """
    Deserialize JSON string to Python object.

    Args:
        json_string: JSON string to deserialize
        strict: Whether to raise on parsing errors

    Returns:
        Python object

    Raises:
        json.JSONDecodeError: If strict and parsing fails
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        if strict:
            raise
        logger.warning("JSON parse error", error=str(e))
        return None


def serialize_datetime(dt: Union[datetime, date, time, str, None]) -> Optional[str]:
    """
    Serialize datetime to ISO format string.

    Args:
        dt: Datetime object or string

    Returns:
        ISO format string or None
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        return dt

    if isinstance(dt, datetime):
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    if isinstance(dt, (date, time)):
        return dt.isoformat()

    return str(dt)


def deserialize_datetime(
    value: Union[str, int, float, None],
    default: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Deserialize string or timestamp to datetime.

    Args:
        value: ISO string or Unix timestamp
        default: Default value if parsing fails

    Returns:
        Datetime object or default
    """
    if value is None:
        return default

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        # Unix timestamp
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (ValueError, OSError):
            return default

    if isinstance(value, str):
        # ISO format string
        try:
            # Handle various ISO formats
            value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(value)
        except ValueError:
            pass

        # Try common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

    return default


def serialize_uuid(value: Union[UUID, str, None]) -> Optional[str]:
    """
    Serialize UUID to string.

    Args:
        value: UUID object or string

    Returns:
        UUID string or None
    """
    if value is None:
        return None

    if isinstance(value, UUID):
        return str(value)

    return value


def deserialize_uuid(value: Union[str, None]) -> Optional[UUID]:
    """
    Deserialize string to UUID.

    Args:
        value: UUID string

    Returns:
        UUID object or None
    """
    if value is None:
        return None

    if isinstance(value, UUID):
        return value

    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def to_camel_case(snake_str: str) -> str:
    """
    Convert snake_case to camelCase.

    Args:
        snake_str: Snake case string

    Returns:
        Camel case string
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """
    Convert camelCase to snake_case.

    Args:
        camel_str: Camel case string

    Returns:
        Snake case string
    """
    import re
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def convert_keys_to_camel(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary keys from snake_case to camelCase.

    Args:
        data: Dictionary with snake_case keys

    Returns:
        Dictionary with camelCase keys
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        new_key = to_camel_case(key)
        if isinstance(value, dict):
            result[new_key] = convert_keys_to_camel(value)
        elif isinstance(value, list):
            result[new_key] = [
                convert_keys_to_camel(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[new_key] = value

    return result


def convert_keys_to_snake(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dictionary keys from camelCase to snake_case.

    Args:
        data: Dictionary with camelCase keys

    Returns:
        Dictionary with snake_case keys
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        new_key = to_snake_case(key)
        if isinstance(value, dict):
            result[new_key] = convert_keys_to_snake(value)
        elif isinstance(value, list):
            result[new_key] = [
                convert_keys_to_snake(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[new_key] = value

    return result


def safe_serialize(data: Any) -> str:
    """
    Safely serialize data, handling potential errors.

    Args:
        data: Data to serialize

    Returns:
        JSON string or error representation
    """
    try:
        return serialize_to_json(data)
    except Exception as e:
        logger.error("Serialization failed", error=str(e))
        return json.dumps({
            "error": "Serialization failed",
            "message": str(e),
            "type": type(data).__name__,
        })


def safe_deserialize(json_string: str) -> Dict[str, Any]:
    """
    Safely deserialize JSON, returning error dict on failure.

    Args:
        json_string: JSON string

    Returns:
        Deserialized data or error dict
    """
    try:
        return deserialize_from_json(json_string) or {}
    except Exception as e:
        logger.error("Deserialization failed", error=str(e))
        return {
            "error": "Deserialization failed",
            "message": str(e),
        }


def bytes_to_json(data: bytes, encoding: str = "utf-8") -> Any:
    """
    Convert bytes to JSON object.

    Args:
        data: Bytes data
        encoding: Character encoding

    Returns:
        Parsed JSON object
    """
    return json.loads(data.decode(encoding))


def json_to_bytes(data: Any, encoding: str = "utf-8") -> bytes:
    """
    Convert JSON object to bytes.

    Args:
        data: JSON-serializable object
        encoding: Character encoding

    Returns:
        Encoded bytes
    """
    return serialize_to_json(data).encode(encoding)
