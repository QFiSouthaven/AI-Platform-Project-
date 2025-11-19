"""
Cache management API endpoints for the Data Integration module.

Provides endpoints for cache operations (get, set, delete, stats).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import settings
from app.models.cache import (
    CacheBatchSetRequest,
    CacheBatchSetResponse,
    CacheDeleteRequest,
    CacheDeleteResponse,
    CacheGetResponse,
    CacheKeyInfo,
    CacheSetRequest,
    CacheSetResponse,
    CacheStats,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_cache_manager(request: Request):
    """Get cache manager from app state."""
    return request.app.state.cache_manager


@router.get("/get/{key:path}", response_model=CacheGetResponse)
async def get_cache_entry(
    key: str,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheGetResponse:
    """
    Get a cache entry by key.

    Args:
        key: Cache key
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheGetResponse with value if found
    """
    try:
        value = await cache_manager.get(key)
        ttl = await cache_manager.get_ttl(key)

        if value is None:
            return CacheGetResponse(
                status="miss",
                key=key,
                value=None,
                ttl_remaining=None,
                timestamp=datetime.now(timezone.utc),
            )

        return CacheGetResponse(
            status="hit",
            key=key,
            value=value,
            ttl_remaining=ttl if ttl > 0 else None,
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error("Failed to get cache entry", key=key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cache entry: {str(e)}")


@router.post("/set", response_model=CacheSetResponse)
async def set_cache_entry(
    cache_request: CacheSetRequest,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheSetResponse:
    """
    Set a cache entry.

    Args:
        cache_request: Cache set request
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheSetResponse with operation result
    """
    try:
        # Build full key with optional namespace
        key = cache_request.key
        if cache_request.namespace:
            key = f"{cache_request.namespace}:{key}"

        # Set the value
        ttl = cache_request.ttl or settings.REDIS_DEFAULT_TTL
        await cache_manager.set(
            key,
            cache_request.value,
            ttl=ttl,
            metadata=cache_request.metadata,
        )

        # Calculate expiration time
        expires_at = None
        if ttl:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        logger.info("Cache entry set", key=key, ttl=ttl)

        return CacheSetResponse(
            status="success",
            key=key,
            ttl=ttl,
            expires_at=expires_at,
            timestamp=datetime.now(timezone.utc),
            message="Cache entry set successfully",
        )

    except Exception as e:
        logger.error("Failed to set cache entry", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to set cache entry: {str(e)}")


@router.post("/set/batch", response_model=CacheBatchSetResponse)
async def set_batch_cache_entries(
    batch_request: CacheBatchSetRequest,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheBatchSetResponse:
    """
    Set multiple cache entries in a batch.

    Args:
        batch_request: Batch of entries to set
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheBatchSetResponse with batch results
    """
    results = []
    successful = 0
    failed = 0

    try:
        if batch_request.atomic:
            # Use pipeline for atomic operation
            await cache_manager.set_many(
                [
                    {
                        "key": (
                            f"{e.namespace}:{e.key}" if e.namespace else e.key
                        ),
                        "value": e.value,
                        "ttl": e.ttl or settings.REDIS_DEFAULT_TTL,
                    }
                    for e in batch_request.entries
                ]
            )

            # All succeeded in atomic mode
            for entry in batch_request.entries:
                key = f"{entry.namespace}:{entry.key}" if entry.namespace else entry.key
                ttl = entry.ttl or settings.REDIS_DEFAULT_TTL
                results.append(
                    CacheSetResponse(
                        status="success",
                        key=key,
                        ttl=ttl,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                successful += 1

        else:
            # Non-atomic: process each entry individually
            for entry in batch_request.entries:
                try:
                    key = f"{entry.namespace}:{entry.key}" if entry.namespace else entry.key
                    ttl = entry.ttl or settings.REDIS_DEFAULT_TTL

                    await cache_manager.set(
                        key,
                        entry.value,
                        ttl=ttl,
                        metadata=entry.metadata,
                    )

                    results.append(
                        CacheSetResponse(
                            status="success",
                            key=key,
                            ttl=ttl,
                            timestamp=datetime.now(timezone.utc),
                        )
                    )
                    successful += 1

                except Exception as e:
                    results.append(
                        CacheSetResponse(
                            status="failed",
                            key=entry.key,
                            ttl=None,
                            timestamp=datetime.now(timezone.utc),
                            message=f"Failed: {str(e)}",
                        )
                    )
                    failed += 1

        return CacheBatchSetResponse(
            status="success" if failed == 0 else "partial",
            total=len(batch_request.entries),
            successful=successful,
            failed=failed,
            results=results,
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error("Failed to set batch cache entries", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch operation failed: {str(e)}")


@router.delete("/delete", response_model=CacheDeleteResponse)
async def delete_cache_entries(
    delete_request: CacheDeleteRequest,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheDeleteResponse:
    """
    Delete cache entries.

    Args:
        delete_request: Delete request with keys/patterns
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheDeleteResponse with deletion results
    """
    try:
        deleted_count = 0
        keys_deleted = []

        # Delete by specific keys
        if delete_request.keys:
            for key in delete_request.keys:
                result = await cache_manager.delete(key)
                if result:
                    deleted_count += 1
                    keys_deleted.append(key)

        # Delete by pattern
        if delete_request.pattern:
            count = await cache_manager.delete_pattern(delete_request.pattern)
            deleted_count += count

        logger.info("Cache entries deleted", count=deleted_count)

        return CacheDeleteResponse(
            status="success",
            deleted_count=deleted_count,
            keys_deleted=keys_deleted,
            timestamp=datetime.now(timezone.utc),
            message=f"Deleted {deleted_count} cache entries",
        )

    except Exception as e:
        logger.error("Failed to delete cache entries", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.delete("/delete/{key:path}", response_model=CacheDeleteResponse)
async def delete_single_cache_entry(
    key: str,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheDeleteResponse:
    """
    Delete a single cache entry by key.

    Args:
        key: Cache key to delete
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheDeleteResponse with deletion result
    """
    try:
        result = await cache_manager.delete(key)

        if not result:
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")

        return CacheDeleteResponse(
            status="success",
            deleted_count=1,
            keys_deleted=[key],
            timestamp=datetime.now(timezone.utc),
            message=f"Cache entry '{key}' deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete cache entry", key=key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.get("/keys", response_model=Dict[str, Any])
async def list_cache_keys(
    request: Request,
    pattern: str = Query("*", description="Pattern to match keys"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum keys to return"),
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    List cache keys matching a pattern.

    Args:
        request: FastAPI request
        pattern: Glob pattern for key matching
        limit: Maximum number of keys to return
        cache_manager: Cache manager instance

    Returns:
        List of matching keys
    """
    try:
        keys = await cache_manager.get_keys(pattern, limit=limit)

        return {
            "status": "success",
            "data": keys,
            "count": len(keys),
            "pattern": pattern,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to list cache keys", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list keys: {str(e)}")


@router.get("/info/{key:path}", response_model=CacheKeyInfo)
async def get_key_info(
    key: str,
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheKeyInfo:
    """
    Get detailed information about a cache key.

    Args:
        key: Cache key
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheKeyInfo with key details
    """
    try:
        info = await cache_manager.get_key_info(key)

        if not info.get("exists"):
            raise HTTPException(status_code=404, detail=f"Key '{key}' not found")

        return CacheKeyInfo(
            key=key,
            type=info.get("type", "unknown"),
            ttl=info.get("ttl", -2),
            memory_usage=info.get("memory_usage", 0),
            encoding=info.get("encoding", "unknown"),
            idle_time=info.get("idle_time", 0),
            exists=info.get("exists", False),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get key info", key=key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get key info: {str(e)}")


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(
    request: Request,
    cache_manager=Depends(get_cache_manager),
) -> CacheStats:
    """
    Get cache statistics.

    Args:
        request: FastAPI request
        cache_manager: Cache manager instance

    Returns:
        CacheStats with cache statistics
    """
    try:
        stats = await cache_manager.get_stats()

        return CacheStats(
            total_keys=stats.get("total_keys", 0),
            memory_used_bytes=stats.get("memory_used_bytes", 0),
            memory_used_human=stats.get("memory_used_human", "0B"),
            hits=stats.get("hits", 0),
            misses=stats.get("misses", 0),
            hit_rate=stats.get("hit_rate", 0.0),
            evicted_keys=stats.get("evicted_keys", 0),
            expired_keys=stats.get("expired_keys", 0),
            connected_clients=stats.get("connected_clients", 0),
            uptime_seconds=stats.get("uptime_seconds", 0),
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error("Failed to get cache stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/flush", response_model=Dict[str, Any])
async def flush_cache(
    request: Request,
    pattern: Optional[str] = Query(None, description="Pattern to flush (default: all)"),
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    Flush cache entries.

    Args:
        request: FastAPI request
        pattern: Optional pattern to flush specific keys
        cache_manager: Cache manager instance

    Returns:
        Flush operation result
    """
    try:
        if pattern:
            deleted = await cache_manager.delete_pattern(pattern)
            message = f"Flushed {deleted} keys matching pattern '{pattern}'"
        else:
            await cache_manager.flush()
            message = "Cache flushed successfully"

        logger.warning("Cache flush performed", pattern=pattern)

        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to flush cache", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to flush cache: {str(e)}")


@router.post("/increment/{key:path}", response_model=Dict[str, Any])
async def increment_counter(
    key: str,
    request: Request,
    amount: int = Query(1, description="Amount to increment"),
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    Increment a counter in cache.

    Args:
        key: Counter key
        request: FastAPI request
        amount: Amount to increment by
        cache_manager: Cache manager instance

    Returns:
        New counter value
    """
    try:
        new_value = await cache_manager.increment(key, amount)

        return {
            "status": "success",
            "key": key,
            "value": new_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to increment counter", key=key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to increment: {str(e)}")


@router.post("/decrement/{key:path}", response_model=Dict[str, Any])
async def decrement_counter(
    key: str,
    request: Request,
    amount: int = Query(1, description="Amount to decrement"),
    cache_manager=Depends(get_cache_manager),
) -> Dict[str, Any]:
    """
    Decrement a counter in cache.

    Args:
        key: Counter key
        request: FastAPI request
        amount: Amount to decrement by
        cache_manager: Cache manager instance

    Returns:
        New counter value
    """
    try:
        new_value = await cache_manager.decrement(key, amount)

        return {
            "status": "success",
            "key": key,
            "value": new_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("Failed to decrement counter", key=key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to decrement: {str(e)}")
