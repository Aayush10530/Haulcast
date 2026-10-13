"""Open-Meteo weather provider adapter."""

import math
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from core.domain import rules_config
from core.domain.grid import cell_center
from core.domain.types import Coordinate, GridCell, HourlySeries, WeatherSeries
from core.providers.base import Cache, ProviderBadResponse
from core.providers.http import execute_request_with_retry

OPENMETEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _normalize_response_item(item: Any) -> tuple[str, dict[str, list[Any]], int]:
    """Validate structure of weather item and return timezone, hourly lists, and count."""
    if not isinstance(item, dict):
        raise ProviderBadResponse("Weather location entry must be a dictionary")

    tz_name = item.get("timezone")
    if not tz_name or not isinstance(tz_name, str):
        raise ProviderBadResponse("Missing timezone in weather response")

    hourly = item.get("hourly")
    if not isinstance(hourly, dict):
        raise ProviderBadResponse("Missing hourly data object in weather response")

    fields = ("time", "wind_speed_10m", "rain", "showers", "snowfall")
    for f in fields:
        lst = hourly.get(f)
        if not isinstance(lst, list) or not lst:
            raise ProviderBadResponse(f"Missing or empty {f} list in hourly data")

    n = len(hourly["time"])
    for f in fields[1:]:
        if len(hourly[f]) != n:
            raise ProviderBadResponse("Hourly array lengths do not match")

    return tz_name, hourly, n


def _validate_timestamp_grid(time_list: list[Any], count: int) -> int:
    """Validate regular 3600-second timestamp grid and return start epoch seconds."""
    try:
        start_epoch = int(time_list[0])
    except (ValueError, TypeError):
        raise ProviderBadResponse("Invalid start epoch in hourly time") from None

    for idx in range(1, count):
        try:
            t = int(time_list[idx])
        except (ValueError, TypeError):
            raise ProviderBadResponse(f"Invalid timestamp at index {idx}") from None
        if t != start_epoch + idx * rules_config.SECONDS_PER_HOUR:
            raise ProviderBadResponse(f"Irregular timestamp step at index {idx}")

    return start_epoch


def _combine_rain_and_showers(
    rain_list: list[Any], showers_list: list[Any]
) -> list[float | None]:
    """Combine hourly rain and showers into unified precipitation rate (in/hr)."""
    rain_vals: list[float | None] = []
    for r, s in zip(rain_list, showers_list, strict=True):
        if r is None or s is None:
            rain_vals.append(None)
            continue
        try:
            rf = float(r)
            sf = float(s)
            rain_vals.append(rf + sf if math.isfinite(rf) and math.isfinite(sf) else None)
        except (ValueError, TypeError):
            rain_vals.append(None)
    return rain_vals


def _parse_numeric_series(values: list[Any]) -> list[float | None]:
    """Extract finite float values or None from a raw API array."""
    parsed: list[float | None] = []
    for val in values:
        if val is None:
            parsed.append(None)
            continue
        try:
            vf = float(val)
            parsed.append(vf if math.isfinite(vf) else None)
        except (ValueError, TypeError):
            parsed.append(None)
    return parsed


def _build_weather_series(
    tz_name: str,
    start_epoch: int,
    wind_vals: list[float | None],
    rain_vals: list[float | None],
    snow_vals: list[float | None],
) -> WeatherSeries:
    """Construct WeatherSeries domain entity from parsed components."""
    return WeatherSeries(
        tz_name=tz_name,
        wind_mph=HourlySeries(start_epoch=start_epoch, values=tuple(wind_vals)),
        rain_in_hr=HourlySeries(start_epoch=start_epoch, values=tuple(rain_vals)),
        snow_in_hr=HourlySeries(start_epoch=start_epoch, values=tuple(snow_vals)),
    )


def _parse_weather_series(item: Any) -> WeatherSeries:
    """Parse a single Open-Meteo location forecast object into WeatherSeries."""
    tz_name, hourly, n = _normalize_response_item(item)
    start_epoch = _validate_timestamp_grid(hourly["time"], n)
    wind_vals = _parse_numeric_series(hourly["wind_speed_10m"])
    rain_vals = _combine_rain_and_showers(hourly["rain"], hourly["showers"])
    snow_vals = _parse_numeric_series(hourly["snowfall"])
    return _build_weather_series(tz_name, start_epoch, wind_vals, rain_vals, snow_vals)


class OpenMeteoWeatherProvider:
    """WeatherProvider adapter for Open-Meteo API."""

    def __init__(
        self,
        cache: Cache,
        ttl_seconds: int = 1800,
        timeout_seconds: float = 8.0,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_workers: int = 4,
    ) -> None:
        self.cache = cache
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self._client = client
        self.sleep = sleep
        self.max_workers = max_workers

    def _execute_request(
        self,
        client: httpx.Client,
        url: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        """Execute HTTP request with at most one retry on 429/5xx/timeout."""
        return execute_request_with_retry(
            client=client,
            url=url,
            params=params,
            service_label="Weather provider",
            sleep_fn=self.sleep,
            check_200=True,
        )

    def _fetch_chunk(
        self,
        chunk: Sequence[GridCell],
        client: httpx.Client,
    ) -> list[WeatherSeries]:
        """Fetch and parse weather series for a chunk of GridCells."""
        centers = [cell_center(c) for c in chunk]
        lat_str = ",".join(str(c.lat) for c in centers)
        lon_str = ",".join(str(c.lon) for c in centers)

        params: dict[str, Any] = {
            "latitude": lat_str,
            "longitude": lon_str,
            "hourly": "wind_speed_10m,rain,showers,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timeformat": "unixtime",
            "timezone": "auto",
            "past_hours": rules_config.WEATHER_PAST_HOURS,
            "forecast_hours": rules_config.WEATHER_FORECAST_HOURS,
        }

        resp = self._execute_request(client, OPENMETEO_FORECAST_URL, params)
        try:
            data = resp.json()
        except Exception:
            raise ProviderBadResponse("Malformed JSON in weather response") from None

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = [data]
        else:
            raise ProviderBadResponse("Unexpected response format from weather provider")

        if len(items) != len(chunk):
            raise ProviderBadResponse(
                f"Expected {len(chunk)} weather items in response, got {len(items)}"
            )

        series_list: list[WeatherSeries] = []
        for idx in range(len(chunk)):
            series_list.append(_parse_weather_series(items[idx]))
        return series_list

    def get_series(self, cells: Sequence[GridCell]) -> dict[GridCell, WeatherSeries]:
        """Fetch weather series for the given grid cells, with caching and chunked batching."""
        if not cells:
            return {}

        # Dedupe cells while preserving order
        unique_cells = list(dict.fromkeys(cells))
        results: dict[GridCell, WeatherSeries] = {}
        missing_cells: list[GridCell] = []

        for cell in unique_cells:
            key = f"wx:{cell.lat_index}:{cell.lon_index}"
            cached = self.cache.get(key)
            if cached is not None and isinstance(cached, WeatherSeries):
                results[cell] = cached
            else:
                missing_cells.append(cell)

        if not missing_cells:
            return results

        chunk_size = rules_config.WEATHER_CHUNK_SIZE
        chunks = [
            missing_cells[i : i + chunk_size] for i in range(0, len(missing_cells), chunk_size)
        ]

        def _process_chunk(chunk_cells: Sequence[GridCell]) -> list[tuple[GridCell, WeatherSeries]]:
            if self._client is not None:
                parsed_series = self._fetch_chunk(chunk_cells, self._client)
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    parsed_series = self._fetch_chunk(chunk_cells, client)

            return list(zip(chunk_cells, parsed_series, strict=True))

        if len(chunks) == 1:
            chunk_results = [_process_chunk(chunks[0])]
        else:
            workers = min(self.max_workers, len(chunks))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                chunk_results = list(executor.map(_process_chunk, chunks))

        for batch in chunk_results:
            for cell, series in batch:
                key = f"wx:{cell.lat_index}:{cell.lon_index}"
                self.cache.set(key, series, ttl_seconds=self.ttl_seconds)
                results[cell] = series

        return results

    def get_timezone(self, coordinate: Coordinate) -> str:
        """Fetch IANA timezone name for a coordinate, cached for 24 hours."""
        lat_rounded = round(coordinate.lat)
        lon_rounded = round(coordinate.lon)
        cache_key = f"tz:{lat_rounded}:{lon_rounded}"

        cached = self.cache.get(cache_key)
        if cached is not None and isinstance(cached, str):
            return cached

        params: dict[str, Any] = {
            "latitude": coordinate.lat,
            "longitude": coordinate.lon,
            "hourly": "temperature_2m",
            "forecast_hours": 1,
            "timezone": "auto",
        }

        def _call(client: httpx.Client) -> httpx.Response:
            return self._execute_request(client, OPENMETEO_FORECAST_URL, params)

        if self._client is not None:
            resp = _call(self._client)
        else:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = _call(client)

        try:
            data = resp.json()
        except Exception:
            raise ProviderBadResponse("Malformed JSON in timezone response") from None

        if isinstance(data, list):
            if not data:
                raise ProviderBadResponse("Empty response from timezone request")
            item = data[0]
        elif isinstance(data, dict):
            item = data
        else:
            raise ProviderBadResponse("Unexpected response format in timezone request")

        tz_name = item.get("timezone")
        if not tz_name or not isinstance(tz_name, str):
            raise ProviderBadResponse("Timezone not found in weather response")

        self.cache.set(cache_key, tz_name, ttl_seconds=86400)
        return tz_name
