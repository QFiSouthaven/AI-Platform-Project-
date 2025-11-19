"""
Redis async client for the Data Integration module.

Provides connection pooling and basic Redis operations.
"""

import asyncio
import sys
from typing import Any, List, Optional, Union

import redis.asyncio as redis
import structlog

# Windows-specific: Ensure proper event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.config import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Async Redis client with connection pooling.

    Provides low-level Redis operations with automatic connection management.
    """

    def __init__(
        self,
        url: str = None,
        max_connections: int = None,
        decode_responses: bool = True,
    ):
        """
        Initialize the Redis client.

        Args:
            url: Redis connection URL
            max_connections: Maximum pool connections
            decode_responses: Whether to decode responses to strings
        """
        self.url = url or settings.REDIS_URL
        self.max_connections = max_connections or settings.REDIS_MAX_CONNECTIONS
        self.decode_responses = decode_responses
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self._pool = redis.ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()
            logger.info(
                "Redis connected",
                url=self._mask_url(self.url),
                max_connections=self.max_connections,
            )

        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        try:
            if self._client:
                await self._client.close()
            if self._pool:
                await self._pool.disconnect()
            logger.info("Redis disconnected")
        except Exception as e:
            logger.error("Error disconnecting from Redis", error=str(e))

    def _mask_url(self, url: str) -> str:
        """Mask password in Redis URL for logging."""
        if "@" in url:
            parts = url.split("@")
            return f"***@{parts[-1]}"
        return url

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return self._client

    async def ping(self) -> bool:
        """
        Check if Redis is reachable.

        Returns:
            True if Redis is reachable
        """
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.

        Args:
            key: Redis key

        Returns:
            Value or None
        """
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: Union[str, bytes],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a value in Redis.

        Args:
            key: Redis key
            value: Value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if set successfully
        """
        return await self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    async def delete(self, *keys: str) -> int:
        """
        Delete keys from Redis.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0
        return await self._client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Args:
            keys: Keys to check

        Returns:
            Number of existing keys
        """
        if not keys:
            return 0
        return await self._client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time on a key.

        Args:
            key: Redis key
            seconds: Expiration time in seconds

        Returns:
            True if timeout was set
        """
        return await self._client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """
        Get TTL for a key.

        Args:
            key: Redis key

        Returns:
            TTL in seconds (-1 if no expire, -2 if not found)
        """
        return await self._client.ttl(key)

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.

        Args:
            pattern: Glob pattern

        Returns:
            List of matching keys
        """
        return await self._client.keys(pattern)

    async def scan(
        self,
        cursor: int = 0,
        match: str = None,
        count: int = 100,
    ) -> tuple:
        """
        Incrementally iterate keys.

        Args:
            cursor: Cursor position
            match: Pattern to match
            count: Number of keys per iteration

        Returns:
            Tuple of (cursor, keys)
        """
        return await self._client.scan(cursor=cursor, match=match, count=count)

    async def mget(self, *keys: str) -> List[Optional[str]]:
        """
        Get multiple keys.

        Args:
            keys: Keys to get

        Returns:
            List of values
        """
        if not keys:
            return []
        return await self._client.mget(*keys)

    async def mset(self, mapping: dict) -> bool:
        """
        Set multiple keys.

        Args:
            mapping: Dict of key-value pairs

        Returns:
            True if successful
        """
        if not mapping:
            return True
        return await self._client.mset(mapping)

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a key.

        Args:
            key: Redis key
            amount: Amount to increment

        Returns:
            New value
        """
        return await self._client.incrby(key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrement a key.

        Args:
            key: Redis key
            amount: Amount to decrement

        Returns:
            New value
        """
        return await self._client.decrby(key, amount)

    async def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get a hash field.

        Args:
            name: Hash name
            key: Field key

        Returns:
            Field value or None
        """
        return await self._client.hget(name, key)

    async def hset(
        self,
        name: str,
        key: str = None,
        value: Any = None,
        mapping: dict = None,
    ) -> int:
        """
        Set hash field(s).

        Args:
            name: Hash name
            key: Field key
            value: Field value
            mapping: Dict of field-value pairs

        Returns:
            Number of fields added
        """
        return await self._client.hset(name, key=key, value=value, mapping=mapping)

    async def hgetall(self, name: str) -> dict:
        """
        Get all hash fields.

        Args:
            name: Hash name

        Returns:
            Dict of field-value pairs
        """
        return await self._client.hgetall(name)

    async def hdel(self, name: str, *keys: str) -> int:
        """
        Delete hash fields.

        Args:
            name: Hash name
            keys: Fields to delete

        Returns:
            Number of fields deleted
        """
        return await self._client.hdel(name, *keys)

    async def lpush(self, name: str, *values) -> int:
        """
        Push values to list.

        Args:
            name: List name
            values: Values to push

        Returns:
            List length after push
        """
        return await self._client.lpush(name, *values)

    async def rpush(self, name: str, *values) -> int:
        """
        Append values to list.

        Args:
            name: List name
            values: Values to append

        Returns:
            List length after push
        """
        return await self._client.rpush(name, *values)

    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        Get list elements.

        Args:
            name: List name
            start: Start index
            end: End index

        Returns:
            List of elements
        """
        return await self._client.lrange(name, start, end)

    async def llen(self, name: str) -> int:
        """
        Get list length.

        Args:
            name: List name

        Returns:
            List length
        """
        return await self._client.llen(name)

    async def sadd(self, name: str, *values) -> int:
        """
        Add members to set.

        Args:
            name: Set name
            values: Members to add

        Returns:
            Number of members added
        """
        return await self._client.sadd(name, *values)

    async def smembers(self, name: str) -> set:
        """
        Get all set members.

        Args:
            name: Set name

        Returns:
            Set of members
        """
        return await self._client.smembers(name)

    async def srem(self, name: str, *values) -> int:
        """
        Remove set members.

        Args:
            name: Set name
            values: Members to remove

        Returns:
            Number of members removed
        """
        return await self._client.srem(name, *values)

    async def flushdb(self) -> bool:
        """
        Flush the current database.

        Returns:
            True if successful
        """
        return await self._client.flushdb()

    async def info(self, section: str = None) -> dict:
        """
        Get Redis server info.

        Args:
            section: Optional section to retrieve

        Returns:
            Server info dict
        """
        return await self._client.info(section)

    async def dbsize(self) -> int:
        """
        Get number of keys in database.

        Returns:
            Number of keys
        """
        return await self._client.dbsize()

    async def type(self, key: str) -> str:
        """
        Get key type.

        Args:
            key: Redis key

        Returns:
            Key type string
        """
        return await self._client.type(key)

    async def memory_usage(self, key: str) -> Optional[int]:
        """
        Get memory usage of a key.

        Args:
            key: Redis key

        Returns:
            Memory usage in bytes or None
        """
        try:
            return await self._client.memory_usage(key)
        except Exception:
            return None

    async def object_encoding(self, key: str) -> Optional[str]:
        """
        Get internal encoding of a key.

        Args:
            key: Redis key

        Returns:
            Encoding type string or None
        """
        try:
            return await self._client.object("encoding", key)
        except Exception:
            return None

    async def object_idletime(self, key: str) -> Optional[int]:
        """
        Get idle time of a key.

        Args:
            key: Redis key

        Returns:
            Idle time in seconds or None
        """
        try:
            return await self._client.object("idletime", key)
        except Exception:
            return None

    def pipeline(self):
        """
        Create a pipeline for batched operations.

        Returns:
            Pipeline object
        """
        return self._client.pipeline()
