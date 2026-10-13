"""TomTom geocoding provider adapter and cached wrapper."""

import time
import urllib.parse
from collections.abc import Callable
from typing import Any

import httpx

from core.domain.types import Coordinate, Place
from core.providers.base import (
    Cache,
    GeocodingProvider,
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from core.providers.http import execute_request_with_retry


class TomTomGeocodingProvider:
    """GeocodingProvider adapter for TomTom Search API v2."""

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 8.0,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key cannot be empty")
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds
        self._client = client
        self.sleep = sleep

    def _execute_request(
        self,
        client: httpx.Client,
        url: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        return execute_request_with_retry(
            client=client,
            url=url,
            params=params,
            service_label="Geocoding",
            sleep_fn=self.sleep,
        )

    def search(self, query: str, limit: int = 5) -> list[Place]:
        """Search US places matching query string up to limit."""
        if not query or not query.strip():
            return []

        quoted = urllib.parse.quote(query.strip())
        url = f"https://api.tomtom.com/search/2/search/{quoted}.json"
        params: dict[str, Any] = {
            "key": self.api_key,
            "typeahead": "true",
            "countrySet": "US",
            "limit": str(limit),
        }

        if self._client is not None:
            resp = self._execute_request(self._client, url, params)
        else:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = self._execute_request(client, url, params)

        if resp.status_code != 200:
            raise ProviderBadResponse("Geocoding provider returned error response")

        try:
            data = resp.json()
        except Exception:
            raise ProviderBadResponse("Geocoding provider returned unparseable JSON") from None

        if not isinstance(data, dict):
            raise ProviderBadResponse("Geocoding provider response must be a JSON object")

        raw_results = data.get("results", [])
        if not isinstance(raw_results, list):
            raise ProviderBadResponse("Geocoding provider results must be a list")

        places: list[Place] = []
        for item in raw_results[:limit]:
            if not isinstance(item, dict):
                raise ProviderBadResponse("Invalid result item in geocoding response")

            pos = item.get("position")
            if not isinstance(pos, dict) or "lat" not in pos or "lon" not in pos:
                raise ProviderBadResponse("Invalid coordinates in geocoding result")

            try:
                lat = float(pos["lat"])
                lon = float(pos["lon"])
                coord = Coordinate(lat=lat, lon=lon)
            except (ValueError, TypeError):
                raise ProviderBadResponse("Invalid coordinate values in geocoding result") from None

            addr = item.get("address", {})
            label = addr.get("freeformAddress") if isinstance(addr, dict) else None
            if not label:
                poi = item.get("poi", {})
                label = poi.get("name") if isinstance(poi, dict) else None
            if not label or not label.strip():
                label = query.strip()

            place_id = str(item.get("id") or f"{lat:.5f},{lon:.5f}")
            places.append(Place(label=label.strip(), coordinate=coord, id=place_id))

        return places


class CachedGeocoding:
    """Caching decorator for GeocodingProvider with 24-hour default TTL."""

    def __init__(
        self,
        provider: GeocodingProvider,
        cache: Cache,
        ttl_seconds: int = 86400,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.ttl_seconds = ttl_seconds

    def search(self, query: str, limit: int = 5) -> list[Place]:
        norm_query = query.strip().lower()
        cache_key = f"geocode:{norm_query}"
        cached = self.cache.get(cache_key)
        if cached is not None and isinstance(cached, list):
            return list(cached[:limit])

        places = self.provider.search(query, limit=limit)
        self.cache.set(cache_key, places, ttl_seconds=self.ttl_seconds)
        return places
