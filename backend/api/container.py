"""Dependency injection container composing providers, services, and cache."""

import datetime
from dataclasses import dataclass
from typing import Any

from core.infra.cache import DjangoCache
from core.providers.base import Cache, GeocodingProvider, RoutingProvider, WeatherProvider
from core.providers.geocoding_tomtom import CachedGeocoding, TomTomGeocodingProvider
from core.providers.routing_tomtom import TomTomRoutingProvider
from core.providers.weather_openmeteo import OpenMeteoWeatherProvider
from core.services.route_selection import RouteSelectionService
from core.services.trip_analysis import TripAnalysisService


@dataclass
class Container:
    """Application dependency container."""

    cache: Cache
    routing: RoutingProvider
    weather: WeatherProvider
    route_selection: RouteSelectionService
    trip_analysis: TripAnalysisService
    geocoding: GeocodingProvider


def build_container(settings: Any) -> Container:
    """Build and compose concrete production container from Django settings."""
    cache = DjangoCache()
    api_key = getattr(settings, "TOMTOM_API_KEY", "").strip() or "unconfigured-key"
    timeout = getattr(settings, "HTTP_TIMEOUT_SECONDS", 8.0)
    route_ttl = getattr(settings, "ROUTE_CACHE_TTL_SECONDS", 1800)
    weather_ttl = getattr(settings, "WEATHER_CACHE_TTL_SECONDS", 1800)
    geocode_ttl = getattr(settings, "GEOCODE_CACHE_TTL_SECONDS", 86400)

    routing = TomTomRoutingProvider(api_key=api_key, timeout_seconds=timeout)
    weather = OpenMeteoWeatherProvider(
        cache=cache,
        ttl_seconds=weather_ttl,
        timeout_seconds=timeout,
    )
    route_selection = RouteSelectionService(
        provider=routing,
        cache=cache,
        ttl_seconds=route_ttl,
    )
    trip_analysis = TripAnalysisService(
        route_selection=route_selection,
        weather=weather,
        clock=lambda: datetime.datetime.now(datetime.UTC),
    )
    raw_geocoding = TomTomGeocodingProvider(api_key=api_key, timeout_seconds=timeout)
    geocoding = CachedGeocoding(provider=raw_geocoding, cache=cache, ttl_seconds=geocode_ttl)

    return Container(
        cache=cache,
        routing=routing,
        weather=weather,
        route_selection=route_selection,
        trip_analysis=trip_analysis,
        geocoding=geocoding,
    )


_container: Container | None = None


def get_container() -> Container:
    """Return lazy singleton application container."""
    global _container
    if _container is None:
        from django.conf import settings

        _container = build_container(settings)
    return _container


def set_container(container: Container | None) -> None:
    """Override singleton container (used in test fixtures)."""
    global _container
    _container = container
