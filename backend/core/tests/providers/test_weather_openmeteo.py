"""Unit tests for OpenMeteoWeatherProvider."""

import json
from collections.abc import Generator
from typing import Any

import httpx
import pytest
import respx

from core.domain.types import Coordinate, GridCell
from core.infra.cache import InMemoryTTLCache
from core.providers.base import (
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from core.providers.weather_openmeteo import (
    OPENMETEO_FORECAST_URL,
    OpenMeteoWeatherProvider,
)


@pytest.fixture(scope="module")
def mock_client() -> Generator[httpx.Client]:
    with httpx.Client() as client:
        yield client


def make_location_payload(
    lat: float,
    lon: float,
    tz_name: str = "America/Chicago",
    start_epoch: int = 1700000000,
    hours_count: int = 6,
    wind: list[float | None] | None = None,
    rain: list[float | None] | None = None,
    showers: list[float | None] | None = None,
    snow: list[float | None] | None = None,
    irregular_step_at: int | None = None,
) -> dict[str, Any]:
    times: list[int] = []
    for i in range(hours_count):
        t = start_epoch + i * 3600
        if irregular_step_at is not None and i == irregular_step_at:
            t += 1800
        times.append(t)

    return {
        "latitude": lat,
        "longitude": lon,
        "timezone": tz_name,
        "timezone_abbreviation": "CST",
        "utc_offset_seconds": -21600,
        "hourly": {
            "time": times,
            "wind_speed_10m": (
                wind if wind is not None else [10.0 + i for i in range(hours_count)]
            ),
            "rain": (rain if rain is not None else [0.05 * i for i in range(hours_count)]),
            "showers": (showers if showers is not None else [0.02 * i for i in range(hours_count)]),
            "snowfall": (snow if snow is not None else [0.0] * hours_count),
        },
    }


@respx.mock(assert_all_mocked=True)
def test_three_location_fixture(respx_mock: respx.MockRouter, mock_client: httpx.Client) -> None:
    cells = [
        GridCell(lat_index=328, lon_index=-968),  # Dallas
        GridCell(lat_index=397, lon_index=-1050),  # Denver
        GridCell(lat_index=419, lon_index=-876),  # Chicago
    ]

    p1 = make_location_payload(32.8, -96.8, tz_name="America/Chicago")
    p2 = make_location_payload(39.7, -105.0, tz_name="America/Denver")
    p3 = make_location_payload(41.9, -87.6, tz_name="America/Chicago")

    route = respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[p1, p2, p3])
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)
    series_map = provider.get_series(cells)

    assert route.called
    assert len(series_map) == 3
    assert series_map[cells[0]].tz_name == "America/Chicago"
    assert series_map[cells[1]].tz_name == "America/Denver"
    assert series_map[cells[2]].tz_name == "America/Chicago"
    assert len(series_map[cells[0]].wind_mph.values) == 6


@respx.mock(assert_all_mocked=True)
def test_single_location_object_response(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    p = make_location_payload(32.8, -96.8, tz_name="America/Chicago")

    # Open-Meteo returns a single dict (not a list) for single coordinate
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=p)
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)
    series_map = provider.get_series([cell])

    assert len(series_map) == 1
    assert cell in series_map
    assert series_map[cell].tz_name == "America/Chicago"


@respx.mock(assert_all_mocked=True)
def test_results_mapped_by_index_even_if_coordinates_differ(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell_a = GridCell(lat_index=328, lon_index=-968)
    cell_b = GridCell(lat_index=397, lon_index=-1050)

    # Returned coordinates differ from requested cell centers
    p_a = make_location_payload(32.78, -96.82, tz_name="America/Chicago")
    p_b = make_location_payload(39.74, -104.99, tz_name="America/Denver")

    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[p_a, p_b])
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)
    series_map = provider.get_series([cell_a, cell_b])

    # Mapped strictly by request index: first is cell_a, second is cell_b
    assert series_map[cell_a].tz_name == "America/Chicago"
    assert series_map[cell_b].tz_name == "America/Denver"


@respx.mock(assert_all_mocked=True)
def test_rain_plus_showers_and_none_propagation(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    # 4 hourly items:
    # 0: 0.10 + 0.05 = 0.15
    # 1: None in showers -> None
    # 2: None in rain -> None
    # 3: NaN in showers -> None
    p = make_location_payload(
        32.8,
        -96.8,
        hours_count=4,
        rain=[0.10, 0.20, None, 0.30],
        showers=[0.05, None, 0.15, float("nan")],
    )

    raw_body = json.dumps(p).encode("utf-8")
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(
            200, content=raw_body, headers={"content-type": "application/json"}
        )
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)
    series_map = provider.get_series([cell])

    rain_vals = series_map[cell].rain_in_hr.values
    assert rain_vals[0] == pytest.approx(0.15)
    assert rain_vals[1] is None
    assert rain_vals[2] is None
    assert rain_vals[3] is None


@respx.mock(assert_all_mocked=True)
def test_irregular_timestamps_raise_bad_response(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    p = make_location_payload(32.8, -96.8, irregular_step_at=2)

    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=p)
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    with pytest.raises(ProviderBadResponse, match="Irregular timestamp step"):
        provider.get_series([cell])


@respx.mock(assert_all_mocked=True)
def test_wrong_count_raises_bad_response(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell1 = GridCell(lat_index=328, lon_index=-968)
    cell2 = GridCell(lat_index=397, lon_index=-1050)
    # Requested 2, returned 1
    p1 = make_location_payload(32.8, -96.8)

    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[p1])
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    with pytest.raises(ProviderBadResponse, match="Expected 2 weather items"):
        provider.get_series([cell1, cell2])


@respx.mock(assert_all_mocked=True)
def test_250_cells_make_exactly_three_calls_and_caching(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cells = [GridCell(lat_index=i, lon_index=0) for i in range(250)]

    def handle_request(request: httpx.Request) -> httpx.Response:
        lat_param = request.url.params.get("latitude", "")
        count = len(lat_param.split(","))
        items = [make_location_payload(float(i), 0.0) for i in range(count)]
        return httpx.Response(200, json=items)

    route = respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(side_effect=handle_request)

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client, max_workers=4)

    # First call: 250 cells chunked into 100, 100, 50 -> exactly 3 HTTP calls
    res = provider.get_series(cells)
    assert len(res) == 250
    assert route.call_count == 3

    # Verify chunk sizes requested
    chunk_sizes = [len(c.request.url.params["latitude"].split(",")) for c in route.calls]
    assert sorted(chunk_sizes) == [50, 100, 100]

    # Second call with the same cells must be served fully from cache
    res2 = provider.get_series(cells)
    assert len(res2) == 250
    assert route.call_count == 3  # No extra HTTP calls made


@respx.mock(assert_all_mocked=True)
def test_partial_cache_hit_fetches_only_missing_cells(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    c1 = GridCell(lat_index=1, lon_index=0)
    c2 = GridCell(lat_index=2, lon_index=0)
    c3 = GridCell(lat_index=3, lon_index=0)

    p1 = make_location_payload(1.0, 0.0)
    p2 = make_location_payload(2.0, 0.0)
    p3 = make_location_payload(3.0, 0.0)

    # Pre-populate cache with c1
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    route_init = respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[p1])
    )
    provider.get_series([c1])
    assert route_init.call_count == 1

    # Now request [c1, c2, c3] -> only c2, c3 should be fetched
    def handle_missing(request: httpx.Request) -> httpx.Response:
        lats = request.url.params.get("latitude", "").split(",")
        assert len(lats) == 2  # Only 2 missing coordinates
        return httpx.Response(200, json=[p2, p3])

    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(side_effect=handle_missing)

    all_series = provider.get_series([c1, c2, c3])
    assert len(all_series) == 3
    assert c1 in all_series and c2 in all_series and c3 in all_series


@respx.mock(assert_all_mocked=True)
def test_429_retried_then_succeeds(respx_mock: respx.MockRouter, mock_client: httpx.Client) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    p = make_location_payload(32.8, -96.8)

    route = respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        side_effect=[
            httpx.Response(429, text="Rate limit exceeded"),
            httpx.Response(200, json=p),
        ]
    )

    sleep_calls: list[float] = []
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(
        cache=cache,
        client=mock_client,
        sleep=sleep_calls.append,
    )

    res = provider.get_series([cell])
    assert len(res) == 1
    assert route.call_count == 2
    assert sleep_calls == [0.3]


@respx.mock(assert_all_mocked=True)
def test_retry_exhausted_raises_provider_rate_limited(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)

    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(429, text="Rate limit exceeded")
    )

    sleep_calls: list[float] = []
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(
        cache=cache,
        client=mock_client,
        sleep=sleep_calls.append,
    )

    with pytest.raises(ProviderRateLimited, match="rate limit exceeded"):
        provider.get_series([cell])
    assert len(sleep_calls) == 1


@respx.mock(assert_all_mocked=True)
def test_get_timezone_cached(respx_mock: respx.MockRouter, mock_client: httpx.Client) -> None:
    coord = Coordinate(lat=32.7767, lon=-96.7970)
    tz_payload = {"timezone": "America/Chicago"}

    route = respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=tz_payload)
    )

    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    tz1 = provider.get_timezone(coord)
    assert tz1 == "America/Chicago"
    assert route.call_count == 1

    # Second call should hit 24h cache
    tz2 = provider.get_timezone(coord)
    assert tz2 == "America/Chicago"
    assert route.call_count == 1


@respx.mock(assert_all_mocked=True)
def test_no_url_appears_in_exception_messages(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    cache = InMemoryTTLCache()
    sleep_calls: list[float] = []

    # Test 500 error
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client, sleep=sleep_calls.append)

    with pytest.raises(ProviderUnavailable) as exc_info:
        provider.get_series([cell])
    msg = str(exc_info.value).lower()
    assert "http" not in msg
    assert "open-meteo" not in msg

    # Test Timeout
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        side_effect=httpx.TimeoutException("Read timed out")
    )
    with pytest.raises(ProviderTimeout) as exc_info_to:
        provider.get_series([cell])
    msg_to = str(exc_info_to.value).lower()
    assert "http" not in msg_to
    assert "open-meteo" not in msg_to


@respx.mock(assert_all_mocked=True)
def test_get_series_empty_and_default_client(
    respx_mock: respx.MockRouter,
) -> None:
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=None)
    assert provider.get_series([]) == {}

    # Test default client lifecycle with get_series
    cell = GridCell(lat_index=328, lon_index=-968)
    p = make_location_payload(32.8, -96.8, hours_count=2)
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=p)
    )
    result = provider.get_series([cell])
    assert cell in result

    # Test default client lifecycle with get_timezone
    coord = Coordinate(lat=32.7767, lon=-96.7970)
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[{"timezone": "America/Chicago"}])
    )
    tz = provider.get_timezone(coord)
    assert tz == "America/Chicago"


@respx.mock(assert_all_mocked=True)
def test_network_and_http_status_errors(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    cache = InMemoryTTLCache()
    sleeps: list[float] = []
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client, sleep=sleeps.append)

    # RequestError retried and raises ProviderUnavailable
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    with pytest.raises(ProviderUnavailable, match="currently unavailable"):
        provider.get_series([cell])
    assert sleeps == [0.3]

    # 401 Auth error raises ProviderUnavailable directly
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(return_value=httpx.Response(401))
    with pytest.raises(ProviderUnavailable, match="authentication failed"):
        provider.get_series([cell])

    # 400 Bad Request raises ProviderBadResponse
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(400, text="Bad Request")
    )
    with pytest.raises(ProviderBadResponse, match="HTTP 400"):
        provider.get_series([cell])


@respx.mock(assert_all_mocked=True)
def test_malformed_response_payloads(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    # Malformed JSON
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(
            200,
            content=b"invalid-json{",
            headers={"content-type": "application/json"},
        )
    )
    with pytest.raises(ProviderBadResponse, match="Malformed JSON"):
        provider.get_series([cell])

    # Non dict / list payload
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json="string-payload")
    )
    with pytest.raises(ProviderBadResponse, match="Unexpected response format"):
        provider.get_series([cell])

    # Item not dict
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=["item-not-dict"])
    )
    with pytest.raises(ProviderBadResponse, match="must be a dictionary"):
        provider.get_series([cell])

    # Item missing timezone
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[{"hourly": {}}])
    )
    with pytest.raises(ProviderBadResponse, match="Missing timezone"):
        provider.get_series([cell])

    # Item missing hourly
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[{"timezone": "UTC"}])
    )
    with pytest.raises(ProviderBadResponse, match="Missing hourly data"):
        provider.get_series([cell])

    # Missing hourly field
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[{"timezone": "UTC", "hourly": {"time": []}}])
    )
    with pytest.raises(ProviderBadResponse, match="Missing or empty"):
        provider.get_series([cell])

    # Hourly array length mismatch
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "timezone": "UTC",
                    "hourly": {
                        "time": [1000],
                        "wind_speed_10m": [10.0, 12.0],
                        "rain": [0.0],
                        "showers": [0.0],
                        "snowfall": [0.0],
                    },
                }
            ],
        )
    )
    with pytest.raises(ProviderBadResponse, match="lengths do not match"):
        provider.get_series([cell])

    # Invalid start epoch
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "timezone": "UTC",
                    "hourly": {
                        "time": ["bad-epoch"],
                        "wind_speed_10m": [10.0],
                        "rain": [0.0],
                        "showers": [0.0],
                        "snowfall": [0.0],
                    },
                }
            ],
        )
    )
    with pytest.raises(ProviderBadResponse, match="Invalid start epoch"):
        provider.get_series([cell])

    # Invalid timestamp at index
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "timezone": "UTC",
                    "hourly": {
                        "time": [1000, "bad-ts"],
                        "wind_speed_10m": [10.0, 10.0],
                        "rain": [0.0, 0.0],
                        "showers": [0.0, 0.0],
                        "snowfall": [0.0, 0.0],
                    },
                }
            ],
        )
    )
    with pytest.raises(ProviderBadResponse, match="Invalid timestamp at index"):
        provider.get_series([cell])


@respx.mock(assert_all_mocked=True)
def test_timezone_error_cases(respx_mock: respx.MockRouter, mock_client: httpx.Client) -> None:
    coord = Coordinate(lat=32.7767, lon=-96.7970)
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    # Malformed JSON
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, content=b"bad-json")
    )
    with pytest.raises(ProviderBadResponse, match="Malformed JSON"):
        provider.get_timezone(coord)

    # Empty list
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=[])
    )
    with pytest.raises(ProviderBadResponse, match="Empty response"):
        provider.get_timezone(coord)

    # Non dict / list
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json="string")
    )
    with pytest.raises(ProviderBadResponse, match="Unexpected response"):
        provider.get_timezone(coord)

    # Missing timezone field
    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json={})
    )
    with pytest.raises(ProviderBadResponse, match="Timezone not found"):
        provider.get_timezone(coord)


@respx.mock(assert_all_mocked=True)
def test_hourly_parsing_fallback_to_none_for_missing_and_invalid_values(
    respx_mock: respx.MockRouter, mock_client: httpx.Client
) -> None:
    cell = GridCell(lat_index=328, lon_index=-968)
    cache = InMemoryTTLCache()
    provider = OpenMeteoWeatherProvider(cache=cache, client=mock_client)

    payload = {
        "latitude": 32.8,
        "longitude": -96.8,
        "timezone": "America/Chicago",
        "hourly": {
            "time": [1700000000, 1700003600, 1700007200],
            "wind_speed_10m": [None, "invalid_wind", 15.0],
            "rain": ["invalid_rain", 0.1, 0.0],
            "showers": [0.0, "invalid_shower", 0.0],
            "snowfall": [None, "invalid_snow", 0.5],
        },
    }

    respx_mock.get(url__startswith=OPENMETEO_FORECAST_URL).mock(
        return_value=httpx.Response(200, json=payload)
    )

    series_map = provider.get_series([cell])
    series = series_map[cell]

    # wind: None, None, 15.0
    assert series.wind_mph.values == (None, None, 15.0)
    # rain: None, None, 0.0
    assert series.rain_in_hr.values == (None, None, 0.0)
    # snow: None, None, 0.5
    assert series.snow_in_hr.values == (None, None, 0.5)
