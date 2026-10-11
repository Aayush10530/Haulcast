"""Cache adapter wrapping Django cache backend and providing in-memory TTL cache."""

import time
from typing import Any

from django.core.cache import cache as default_django_cache
from django.core.cache.backends.base import BaseCache


class DjangoCache:
    """Cache implementation wrapping Django's configured cache backend."""

    def __init__(self, backend: BaseCache | None = None) -> None:
        self._cache = backend if backend is not None else default_django_cache

    def get(self, key: str) -> Any | None:
        """Retrieve value from cache by string key."""
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store value in cache with a TTL in seconds."""
        self._cache.set(key, value, timeout=ttl_seconds)

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        self._cache.delete(key)

    def clear(self) -> None:
        """Clear all entries from cache backend."""
        self._cache.clear()


class InMemoryTTLCache:
    """In-memory cache with TTL support for testing or non-Django execution."""

    def __init__(self, default_ttl_seconds: int = 1800) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self.default_ttl_seconds = default_ttl_seconds

    def get(self, key: str) -> Any | None:
        """Retrieve value if key exists and has not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, val = entry
        if time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store value with TTL in seconds."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires_at = time.monotonic() + ttl
        self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        """Remove key from in-memory cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all entries."""
        self._store.clear()
