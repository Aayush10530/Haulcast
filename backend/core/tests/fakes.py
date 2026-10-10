"""In-memory test doubles for external providers and cache."""

from collections.abc import Sequence
from typing import Any

from core.domain.types import Coordinate, GridCell, Place, RawRoute, WeatherSeries
from core.providers.base import ProviderError


class FakeRoutingProvider:
    """In-memory fake implementation of RoutingProvider."""

    def __init__(
        self,
        routes: list[RawRoute] | None = None,
        error: ProviderError | None = None,
    ) -> None:
        self.routes = routes or []
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        via: Sequence[Coordinate] = (),
        max_routes: int = 3,
    ) -> list[RawRoute]:
        self.calls.append(
            {
                "origin": origin,
                "destination": destination,
                "via": tuple(via),
                "max_routes": max_routes,
            }
        )
        if self.error is not None:
            raise self.error
        return list(self.routes[:max_routes])


class FakeGeocodingProvider:
    """In-memory fake implementation of GeocodingProvider."""

    def __init__(
        self,
        places_by_query: dict[str, list[Place]] | None = None,
        error: ProviderError | None = None,
    ) -> None:
        self.places_by_query = places_by_query or {}
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def search(self, query: str, limit: int = 5) -> list[Place]:
        self.calls.append({"query": query, "limit": limit})
        if self.error is not None:
            raise self.error
        return list(self.places_by_query.get(query, [])[:limit])


class FakeWeatherProvider:
    """In-memory fake implementation of WeatherProvider."""

    def __init__(
        self,
        series_by_cell: dict[GridCell, WeatherSeries] | None = None,
        timezone: str = "America/Chicago",
        error: ProviderError | None = None,
    ) -> None:
        self.series_by_cell = series_by_cell or {}
        self.timezone = timezone
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def get_series(self, cells: Sequence[GridCell]) -> dict[GridCell, WeatherSeries]:
        self.calls.append({"cells": tuple(cells)})
        if self.error is not None:
            raise self.error
        return {c: self.series_by_cell[c] for c in cells if c in self.series_by_cell}

    def get_timezone(self, coordinate: Coordinate) -> str:
        self.calls.append({"coordinate": coordinate})
        if self.error is not None:
            raise self.error
        return self.timezone


class FakeCache:
    """In-memory fake implementation of Cache."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
