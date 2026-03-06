import redis
import json
import hashlib
import pickle
from django.conf import settings
from django.core.cache import cache
from functools import wraps
from typing import Any, Callable, Optional, Union

# Redis client setup
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


class RedisCache:
    """
    Redis cache utility
    """

    # Default timeouts (in seconds)
    DEFAULT_TIMEOUT = 300  # 5 minutes
    DEFAULT_VERSION_TIMEOUT = 86400  # 24 hours for version keys

    def __init__(
        self, prefix: str = "", timeout: int = DEFAULT_TIMEOUT, versioned: bool = True
    ):
        self.prefix = prefix
        self.timeout = timeout
        self.versioned = versioned

    def _make_key(self, key: str) -> str:
        """Create a namespaced cache key"""
        if self.prefix:
            return f"{self.prefix}:{key}"
        return key

    def _get_version(self, prefix: str = None) -> int:
        """Get current version for a prefix"""
        version_key = f"version:{prefix or self.prefix}"
        version = redis_client.get(version_key)
        if version is None:
            version = 1
            redis_client.setex(version_key, self.DEFAULT_VERSION_TIMEOUT, version)
        return int(version)

    def _increment_version(self, prefix: str = None) -> int:
        """Increment version for a prefix (invalidates cache)"""
        version_key = f"version:{prefix or self.prefix}"
        version = redis_client.incr(version_key)
        # Reset expiry
        redis_client.expire(version_key, self.DEFAULT_VERSION_TIMEOUT)
        return version

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache"""
        cache_key = self._make_key(key)

        if self.versioned:
            version = self._get_version()
            cache_key = f"{cache_key}:v{version}"

        data = redis_client.get(cache_key)
        if data:
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(data.encode("latin1"))
                except:
                    return data
        return default

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set a value in cache"""
        cache_key = self._make_key(key)

        if self.versioned:
            version = self._get_version()
            cache_key = f"{cache_key}:v{version}"

        # Try JSON first, fallback to pickle for complex objects
        try:
            data = json.dumps(value)
        except (TypeError, ValueError):
            data = pickle.dumps(value).decode("latin1")

        return redis_client.setex(cache_key, timeout or self.timeout, data)

    def get_or_set(
        self, key: str, func: Callable, timeout: Optional[int] = None
    ) -> Any:
        """Get from cache or set using callable if not exists"""
        value = self.get(key)
        if value is not None:
            return value

        value = func()
        self.set(key, value, timeout)
        return value

    def delete(self, key: str) -> int:
        """Delete a specific key"""
        cache_key = self._make_key(key)
        if self.versioned:
            # Delete all versions? Or just current?
            version = self._get_version()
            return redis_client.delete(f"{cache_key}:v{version}")
        return redis_client.delete(cache_key)

    def invalidate(self, prefix: str = None) -> int:
        """Invalidate all cache entries with given prefix by incrementing version"""
        return self._increment_version(prefix)

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # Decorator for views/functions
    def decorator(
        self, key_func: Optional[Callable] = None, timeout: Optional[int] = None
    ):
        """
        Decorator for caching function results

        Args:
            key_func: Optional function to generate cache key from args/kwargs
            timeout: Optional custom timeout for this specific cached function
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func and callable(key_func):
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    cache_key = hashlib.md5(
                        f"{func.__name__}:{args}:{kwargs}".encode()
                    ).hexdigest()

                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function
                result = func(*args, **kwargs)

                # Cache result
                self.set(cache_key, result, timeout or self.timeout)

                return result

            return wrapper

        return decorator


# Singleton instances for different use cases
default_cache = RedisCache()
view_cache = RedisCache(prefix="views", timeout=60)  # 1 minute for views
model_cache = RedisCache(prefix="models", timeout=3600)  # 1 hour for models


# Helper functions for easy import
def cache_get(key: str, default: Any = None) -> Any:
    """Global cache get"""
    return default_cache.get(key, default)


def cache_set(key: str, value: Any, timeout: Optional[int] = None) -> bool:
    """Global cache set"""
    return default_cache.set(key, value, timeout)


def cache_invalidate(prefix: str) -> int:
    """Global cache invalidation"""
    return default_cache.invalidate(prefix)
