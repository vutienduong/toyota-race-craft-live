"""
Caching utilities for performance optimization
Supports both in-memory and Redis caching
"""

import json
import hashlib
import time
from typing import Any, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Flexible cache manager supporting multiple backends
    """

    def __init__(self, backend: str = "memory", redis_url: Optional[str] = None, default_ttl: int = 300):
        """
        Args:
            backend: Cache backend ("memory" or "redis")
            redis_url: Redis connection URL (optional)
            default_ttl: Default time-to-live in seconds
        """
        self.backend = backend
        self.default_ttl = default_ttl
        self._memory_cache = {}
        self._memory_expiry = {}
        self.redis_client = None

        if backend == "redis":
            try:
                import redis
                self.redis_client = redis.from_url(redis_url or "redis://localhost:6379/0")
                logger.info("Redis cache initialized")
            except ImportError:
                logger.warning("Redis not available, falling back to memory cache")
                self.backend = "memory"
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using memory cache")
                self.backend = "memory"

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        # Create a stable string representation
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

        key_string = ":".join(key_parts)

        # Hash for consistent length
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.backend == "redis" and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return None
        else:
            # Memory cache
            if key in self._memory_cache:
                # Check expiry
                if key in self._memory_expiry:
                    if time.time() < self._memory_expiry[key]:
                        return self._memory_cache[key]
                    else:
                        # Expired, remove
                        del self._memory_cache[key]
                        del self._memory_expiry[key]
                else:
                    return self._memory_cache[key]

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.default_ttl

        if self.backend == "redis" and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                return False
        else:
            # Memory cache
            self._memory_cache[key] = value
            self._memory_expiry[key] = time.time() + ttl
            return True

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if self.backend == "redis" and self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                return False
        else:
            # Memory cache
            if key in self._memory_cache:
                del self._memory_cache[key]
            if key in self._memory_expiry:
                del self._memory_expiry[key]
            return True

    def clear(self) -> bool:
        """Clear all cache entries"""
        if self.backend == "redis" and self.redis_client:
            try:
                self.redis_client.flushdb()
                return True
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
                return False
        else:
            self._memory_cache.clear()
            self._memory_expiry.clear()
            return True

    def cleanup_expired(self):
        """Cleanup expired entries (memory cache only)"""
        if self.backend == "memory":
            current_time = time.time()
            expired_keys = [
                key for key, expiry in self._memory_expiry.items()
                if current_time >= expiry
            ]

            for key in expired_keys:
                del self._memory_cache[key]
                del self._memory_expiry[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(backend="memory", default_ttl=300)
    return _cache_manager


def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds (None = use default)

    Example:
        @cached("pace_forecast", ttl=60)
        def get_pace_forecast(vehicle_id: str, lap: int):
            # Expensive computation
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Generate cache key
            cache_key = cache._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {prefix}")
                return cached_value

            # Cache miss - compute value
            logger.debug(f"Cache miss for {prefix}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl)

            return result

        # Add cache control methods
        wrapper.clear_cache = lambda: get_cache_manager().clear()
        wrapper.invalidate = lambda *args, **kwargs: get_cache_manager().delete(
            get_cache_manager()._generate_key(prefix, *args, **kwargs)
        )

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize cache
    cache = CacheManager(backend="memory")

    # Set value
    cache.set("test_key", {"data": "test_value"}, ttl=60)

    # Get value
    value = cache.get("test_key")
    print(f"Cached value: {value}")

    # Test decorator
    @cached("expensive_function", ttl=120)
    def expensive_function(x: int, y: int) -> int:
        print("Computing...")
        time.sleep(1)
        return x + y

    # First call - cache miss
    result1 = expensive_function(5, 3)
    print(f"Result 1: {result1}")

    # Second call - cache hit (instant)
    result2 = expensive_function(5, 3)
    print(f"Result 2: {result2}")

    # Different arguments - cache miss
    result3 = expensive_function(10, 20)
    print(f"Result 3: {result3}")
