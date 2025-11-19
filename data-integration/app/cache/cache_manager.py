"""
Cache manager for the Data Integration module.

Provides high-level cache operations with JSON serialization and metadata support.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from app.cache.redis_client import RedisClient
from app.config import settings

logger = structlog.get_logger(__name__)


class CacheManager:
    """
    High-level cache manager with JSON serialization.

    Provides convenient cache operations with automatic serialization,
    TTL management, and statistics tracking.
    """

    def __init__(self, redis_client: RedisClient):
        """
        Initialize the cache manager.

        Args:
            redis_client: RedisClient instance
        """
        self.redis = redis_client
        self._prefix = settings.CACHE_KEY_PREFIX
        self._default_ttl = settings.CACHE_DEFAULT_TTL
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }

    def _make_key(self, key: str) -> str:
        """
        Create a prefixed cache key.

        Args:
            key: Original key

        Returns:
            Prefixed key
        """
        if self._prefix and not key.startswith(self._prefix):
            return f"{self._prefix}:{key}"
        return key

    def _serialize(self, value: Any) -> str:
        """
        Serialize a value to JSON string.

        Args:
            value: Value to serialize

        Returns:
            JSON string
        """
        def json_encoder(obj):
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "model_dump"):
                return obj.model_dump()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(value, default=json_encoder)

    def _deserialize(self, value: Optional[str]) -> Any:
        """
        Deserialize a JSON string to Python object.

        Args:
            value: JSON string

        Returns:
            Python object
        """
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def get(self, key: str) -> Any:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        full_key = self._make_key(key)
        value = await self.redis.get(full_key)

        if value is not None:
            self._stats["hits"] += 1
            return self._deserialize(value)

        self._stats["misses"] += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            metadata: Optional metadata to store with value

        Returns:
            True if successful
        """
        full_key = self._make_key(key)
        ttl = ttl or self._default_ttl

        # Wrap value with metadata if provided
        if metadata:
            wrapped_value = {
                "_value": value,
                "_metadata": metadata,
                "_cached_at": datetime.now(timezone.utc).isoformat(),
            }
            serialized = self._serialize(wrapped_value)
        else:
            serialized = self._serialize(value)

        result = await self.redis.set(full_key, serialized, ex=ttl)
        self._stats["sets"] += 1

        logger.debug("Cache set", key=key, ttl=ttl)
        return result

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        full_key = self._make_key(key)
        result = await self.redis.delete(full_key)
        self._stats["deletes"] += 1

        logger.debug("Cache delete", key=key, result=result)
        return result > 0

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        full_key = self._make_key(key)
        return await self.redis.exists(full_key) > 0

    async def get_ttl(self, key: str) -> int:
        """
        Get TTL for a cache key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds (-1 if no expire, -2 if not found)
        """
        full_key = self._make_key(key)
        return await self.redis.ttl(full_key)

    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Set TTL for an existing key.

        Args:
            key: Cache key
            ttl: New TTL in seconds

        Returns:
            True if successful
        """
        full_key = self._make_key(key)
        return await self.redis.expire(full_key, ttl)

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dict mapping keys to values
        """
        if not keys:
            return {}

        full_keys = [self._make_key(k) for k in keys]
        values = await self.redis.mget(*full_keys)

        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                self._stats["hits"] += 1
                result[key] = self._deserialize(value)
            else:
                self._stats["misses"] += 1

        return result

    async def set_many(
        self,
        items: List[Dict[str, Any]],
        default_ttl: Optional[int] = None,
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            items: List of {key, value, ttl} dicts
            default_ttl: Default TTL if not specified per item

        Returns:
            True if successful
        """
        if not items:
            return True

        pipeline = self.redis.pipeline()

        for item in items:
            key = self._make_key(item["key"])
            value = self._serialize(item["value"])
            ttl = item.get("ttl", default_ttl or self._default_ttl)

            pipeline.set(key, value, ex=ttl)
            self._stats["sets"] += 1

        await pipeline.execute()
        return True

    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple keys from cache.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0

        full_keys = [self._make_key(k) for k in keys]
        deleted = await self.redis.delete(*full_keys)
        self._stats["deletes"] += deleted

        return deleted

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching a pattern.

        Args:
            pattern: Glob pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern)
        keys = await self.redis.keys(full_pattern)

        if not keys:
            return 0

        deleted = await self.redis.delete(*keys)
        self._stats["deletes"] += deleted

        logger.debug("Pattern delete", pattern=pattern, deleted=deleted)
        return deleted

    async def get_keys(
        self, pattern: str = "*", limit: int = 1000
    ) -> List[str]:
        """
        Get keys matching a pattern.

        Args:
            pattern: Glob pattern
            limit: Maximum number of keys to return

        Returns:
            List of matching keys
        """
        full_pattern = self._make_key(pattern)
        keys = []
        cursor = 0

        while True:
            cursor, batch = await self.redis.scan(
                cursor=cursor,
                match=full_pattern,
                count=100,
            )
            keys.extend(batch)

            if cursor == 0 or len(keys) >= limit:
                break

        # Remove prefix from keys
        if self._prefix:
            prefix_len = len(self._prefix) + 1
            keys = [k[prefix_len:] if k.startswith(self._prefix) else k for k in keys]

        return keys[:limit]

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.

        Args:
            key: Counter key
            amount: Amount to increment

        Returns:
            New value
        """
        full_key = self._make_key(key)
        return await self.redis.incr(full_key, amount)

    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement a counter.

        Args:
            key: Counter key
            amount: Amount to decrement

        Returns:
            New value
        """
        full_key = self._make_key(key)
        return await self.redis.decr(full_key, amount)

    async def get_or_set(
        self,
        key: str,
        default_factory: callable,
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get a value or set it using a factory function.

        Args:
            key: Cache key
            default_factory: Async function to generate value if missing
            ttl: TTL for new value

        Returns:
            Cached or generated value
        """
        value = await self.get(key)
        if value is not None:
            return value

        # Generate and cache new value
        value = await default_factory()
        await self.set(key, value, ttl=ttl)

        return value

    async def flush(self) -> None:
        """Flush all cached data."""
        await self.redis.flushdb()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
        logger.warning("Cache flushed")

    async def get_key_info(self, key: str) -> Dict[str, Any]:
        """
        Get detailed information about a cache key.

        Args:
            key: Cache key

        Returns:
            Dict with key information
        """
        full_key = self._make_key(key)

        exists = await self.redis.exists(full_key) > 0
        if not exists:
            return {"exists": False}

        return {
            "exists": True,
            "type": await self.redis.type(full_key),
            "ttl": await self.redis.ttl(full_key),
            "memory_usage": await self.redis.memory_usage(full_key) or 0,
            "encoding": await self.redis.object_encoding(full_key) or "unknown",
            "idle_time": await self.redis.object_idletime(full_key) or 0,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict containing cache stats
        """
        # Get Redis server info
        info = await self.redis.info("memory")
        stats_info = await self.redis.info("stats")
        server_info = await self.redis.info("server")
        client_info = await self.redis.info("clients")

        # Calculate hit rate
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )

        # Format memory usage
        memory_bytes = info.get("used_memory", 0)
        memory_human = self._format_bytes(memory_bytes)

        return {
            "total_keys": await self.redis.dbsize(),
            "memory_used_bytes": memory_bytes,
            "memory_used_human": memory_human,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "evicted_keys": stats_info.get("evicted_keys", 0),
            "expired_keys": stats_info.get("expired_keys", 0),
            "connected_clients": client_info.get("connected_clients", 0),
            "uptime_seconds": server_info.get("uptime_in_seconds", 0),
        }

    def _format_bytes(self, size: int) -> str:
        """
        Format byte size to human-readable string.

        Args:
            size: Size in bytes

        Returns:
            Formatted string
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
        return f"{size:.2f}PB"

    def reset_stats(self) -> None:
        """Reset local statistics."""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
        logger.info("Cache manager stats reset")
