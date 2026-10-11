"""Unit tests for cache adapters."""

import time

from django.core.cache import cache as default_django_cache
from django.core.cache.backends.locmem import LocMemCache

from core.domain.types import Coordinate, GridCell
from core.infra.cache import DjangoCache, InMemoryTTLCache


def test_django_cache_with_locmem() -> None:
    cache = DjangoCache(default_django_cache)
    cache.clear()

    assert cache.get("test_key") is None
    cache.set("test_key", "sample_value", ttl_seconds=60)
    assert cache.get("test_key") == "sample_value"

    # Test pickled complex objects (Coordinate, GridCell)
    coord = Coordinate(lat=32.7767, lon=-96.7970)
    cell = GridCell(lat_index=328, lon_index=-968)
    cache.set("coord_key", coord, ttl_seconds=60)
    cache.set("cell_key", cell, ttl_seconds=60)

    assert cache.get("coord_key") == coord
    assert cache.get("cell_key") == cell

    cache.delete("coord_key")
    assert cache.get("coord_key") is None

    cache.clear()
    assert cache.get("cell_key") is None
    assert cache.get("test_key") is None


def test_django_cache_isolated_backend() -> None:
    isolated_backend = LocMemCache("isolated_test_cache", {})
    cache = DjangoCache(isolated_backend)
    cache.set("foo", "bar", ttl_seconds=10)
    assert cache.get("foo") == "bar"
    cache.delete("foo")
    assert cache.get("foo") is None


def test_in_memory_ttl_cache() -> None:
    cache = InMemoryTTLCache(default_ttl_seconds=3600)
    assert cache.get("missing") is None

    cache.set("k1", "v1", ttl_seconds=3600)
    assert cache.get("k1") == "v1"

    cache.delete("k1")
    assert cache.get("k1") is None

    # Test TTL expiration with 0 second TTL
    cache.set("short_lived", "expired_val", ttl_seconds=0)
    # Give a tiny sleep to exceed monotonic clock
    time.sleep(0.005)
    assert cache.get("short_lived") is None

    cache.set("k2", "v2")
    assert cache.get("k2") == "v2"
    cache.clear()
    assert cache.get("k2") is None
