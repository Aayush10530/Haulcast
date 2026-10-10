"""Provider protocols and typed error hierarchy."""

from collections.abc import Sequence
from typing import Any, Protocol

from core.domain.types import Coordinate, GridCell, Place, RawRoute, WeatherSeries


class ProviderError(Exception):
    """Base error for third-party provider failures."""


class ProviderTimeout(ProviderError):
    """Provider request timed out."""


class ProviderRateLimited(ProviderError):
    """Provider rate limit (HTTP 429) was reached."""


class ProviderBadResponse(ProviderError):
    """Provider returned malformed, unparseable, or inconsistent data."""


class ProviderUnavailable(ProviderError):
    """Provider service is unavailable (HTTP 5xx, 401/403, or connection failure)."""


class NoRouteFound(ProviderError):
    """Provider could not find a route between the requested coordinates."""


class RoutingProvider(Protocol):
    """Protocol for routing engine adapters."""

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        via: Sequence[Coordinate] = (),
        max_routes: int = 3,
    ) -> list[RawRoute]: ...


class GeocodingProvider(Protocol):
    """Protocol for address geocoding and search adapters."""

    def search(self, query: str, limit: int = 5) -> list[Place]: ...


class WeatherProvider(Protocol):
    """Protocol for weather forecast adapters."""

    def get_series(self, cells: Sequence[GridCell]) -> dict[GridCell, WeatherSeries]: ...

    def get_timezone(self, coordinate: Coordinate) -> str: ...


class Cache(Protocol):
    """Protocol for application caching adapters."""

    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any, ttl_seconds: int) -> None: ...
