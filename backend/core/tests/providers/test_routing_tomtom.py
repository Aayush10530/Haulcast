"""Tests for TomTomRoutingProvider and provider base interfaces."""

import json
import logging
import math
from collections.abc import Generator
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from core.domain.types import Coordinate, GridCell, Place, RawRoute, Timeline
from core.providers.base import (
    Cache,
    GeocodingProvider,
    NoRouteFound,
    ProviderBadResponse,
    ProviderError,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
    RoutingProvider,
    WeatherProvider,
)
from core.providers.routing_tomtom import TomTomRoutingProvider
from core.tests.fakes import (
    FakeCache,
    FakeGeocodingProvider,
    FakeRoutingProvider,
    FakeWeatherProvider,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _load_fixture(filename: str) -> dict[str, Any]:
    with open(FIXTURES_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mock_client() -> Generator[httpx.Client]:
    with httpx.Client() as client:
        yield client


@pytest.fixture
def tomtom_3_routes_data() -> dict[str, Any]:
    return _load_fixture("tomtom_3_routes.json")


@pytest.fixture
def tomtom_via_route_data() -> dict[str, Any]:
    return _load_fixture("tomtom_via_route.json")


@pytest.fixture
def tomtom_no_route_data() -> dict[str, Any]:
    return _load_fixture("tomtom_no_route.json")


# Configure respx router so any unmocked request fails immediately
respx.mock.assert_all_mocked = True


# ---------------------------------------------------------------------------
# Success scenarios
# ---------------------------------------------------------------------------


@respx.mock
def test_tomtom_success_three_routes(
    tomtom_3_routes_data: dict[str, Any], mock_client: httpx.Client
) -> None:
    origin = Coordinate(lat=34.0522, lon=-118.2437)
    destination = Coordinate(lat=40.7608, lon=-111.8910)

    route_mock = respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/34.0522,-118.2437:40.7608,-111.891/json"
    ).mock(return_value=httpx.Response(200, json=tomtom_3_routes_data))

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)
    routes = provider.get_routes(origin, destination, max_routes=3)

    assert route_mock.called
    req = route_mock.calls.last.request
    assert req.url.params["travelMode"] == "truck"
    assert req.url.params["traffic"] == "false"
    assert req.url.params["vehicleMaxSpeed"] == "105"
    assert req.url.params["instructionsType"] == "tagged"
    assert req.url.params["maxAlternatives"] == "2"

    assert len(routes) == 3
    assert not sleep_calls

    for idx, r in enumerate(routes):
        assert isinstance(r, RawRoute)
        assert r.provider_id == f"tomtom_{idx}"
        assert len(r.polyline) >= 2
        assert r.distance_miles > 0.0
        assert r.duration_seconds > 0.0
        assert isinstance(r.timeline, Timeline)
        assert r.timeline.distances_miles[0] == 0.0
        assert r.timeline.elapsed_seconds[0] == 0.0
        assert math.isclose(r.timeline.distances_miles[-1], r.distance_miles, rel_tol=1e-5)
        assert math.isclose(r.timeline.elapsed_seconds[-1], r.duration_seconds, rel_tol=1e-5)


@respx.mock
def test_tomtom_via_request_two_legs(
    tomtom_via_route_data: dict[str, Any], mock_client: httpx.Client
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    via = Coordinate(lat=33.5779, lon=-101.8552)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    route_mock = respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:33.5779,-101.8552:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=tomtom_via_route_data))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    routes = provider.get_routes(origin, destination, via=[via], max_routes=3)

    assert route_mock.called
    req = route_mock.calls.last.request
    assert req.url.params["maxAlternatives"] == "0"
    assert len(routes) == 1
    route = routes[0]
    assert len(route.polyline) == 39  # Duplicate junction point dropped
    assert route.distance_miles > 0.0
    assert route.duration_seconds > 0.0


# ---------------------------------------------------------------------------
# Error mappings & retries
# ---------------------------------------------------------------------------


@respx.mock
def test_tomtom_timeout_retry_and_exhaustion(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(side_effect=httpx.ReadTimeout("Connection read timed out"))

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)

    with pytest.raises(ProviderTimeout) as exc_info:
        provider.get_routes(origin, destination)

    assert "timed out" in str(exc_info.value).lower()
    assert sleep_calls == [0.3]


@respx.mock
def test_tomtom_rate_limited_retry_and_exhaustion(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(429, text="Rate limit exceeded"))

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)

    with pytest.raises(ProviderRateLimited) as exc_info:
        provider.get_routes(origin, destination)

    assert "rate limit" in str(exc_info.value).lower()
    assert sleep_calls == [0.3]


@pytest.mark.parametrize("status_code", [401, 403])
@respx.mock
def test_tomtom_auth_failure_no_retry(status_code: int, mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(status_code, text="Forbidden"))

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)

    with pytest.raises(ProviderUnavailable) as exc_info:
        provider.get_routes(origin, destination)

    assert "authentication failed" in str(exc_info.value).lower()
    assert not sleep_calls


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
@respx.mock
def test_tomtom_server_error_retry_and_exhaustion(
    status_code: int, mock_client: httpx.Client
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(status_code, text="Internal Server Error"))

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)

    with pytest.raises(ProviderUnavailable) as exc_info:
        provider.get_routes(origin, destination)

    assert "unavailable" in str(exc_info.value).lower()
    assert sleep_calls == [0.3]


@respx.mock
def test_tomtom_connection_error_retry_and_exhaustion(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(side_effect=httpx.ConnectError("Connection refused"))

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)

    with pytest.raises(ProviderUnavailable) as exc_info:
        provider.get_routes(origin, destination)

    assert "unavailable" in str(exc_info.value).lower()
    assert sleep_calls == [0.3]


@respx.mock
def test_tomtom_retry_then_success(
    tomtom_via_route_data: dict[str, Any], mock_client: httpx.Client
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    route_mock = respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    )
    route_mock.side_effect = [
        httpx.Response(500, text="Temporary Error"),
        httpx.Response(200, json=tomtom_via_route_data),
    ]

    sleep_calls: list[float] = []
    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=sleep_calls.append)
    routes = provider.get_routes(origin, destination)

    assert len(routes) == 1
    assert sleep_calls == [0.3]


# ---------------------------------------------------------------------------
# Bad response / Malformed body / No route found
# ---------------------------------------------------------------------------


@respx.mock
def test_tomtom_malformed_json_syntax(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, text="not-valid-json{["))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(ProviderBadResponse) as exc_info:
        provider.get_routes(origin, destination)

    assert "unparseable json" in str(exc_info.value).lower()


@respx.mock
def test_tomtom_json_not_a_dict(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=["unexpected", "array"]))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(ProviderBadResponse):
        provider.get_routes(origin, destination)


@pytest.mark.parametrize(
    "payload",
    [
        {"routes": ["not_a_dict"]},
        {"routes": [{"summary": None, "legs": []}]},
        {"routes": [{"summary": {}, "legs": []}]},
        {"routes": [{"summary": {"lengthInMeters": 100}, "legs": []}]},
        {"routes": [{"summary": {"lengthInMeters": 100, "travelTimeInSeconds": 10}, "legs": []}]},
        {
            "routes": [
                {
                    "summary": {"lengthInMeters": 100, "travelTimeInSeconds": 10},
                    "legs": [{"points": [{"latitude": 1.0}]}],
                }
            ]
        },
        {
            "routes": [
                {
                    "summary": {"lengthInMeters": 100, "travelTimeInSeconds": 10},
                    "legs": [
                        {
                            "points": [
                                {"latitude": 1.0, "longitude": 2.0},
                                {"latitude": "invalid", "longitude": 2.0},
                            ]
                        }
                    ],
                }
            ]
        },
        {
            "routes": [
                {
                    "summary": {"lengthInMeters": 100, "travelTimeInSeconds": 10},
                    "legs": [
                        {
                            "points": [
                                {"latitude": 1.0, "longitude": 2.0},
                                {"latitude": 3.0, "longitude": 4.0},
                            ]
                        }
                    ],
                    "guidance": {
                        "instructions": [{"routeOffsetInMeters": 50, "travelTimeInSeconds": -10}]
                    },
                }
            ]
        },
    ],
)
@respx.mock
def test_tomtom_malformed_route_structures(
    payload: dict[str, Any], mock_client: httpx.Client
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=payload))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(ProviderBadResponse):
        provider.get_routes(origin, destination)


@respx.mock
def test_tomtom_empty_routes_list_raises_no_route_found(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json={"routes": []}))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(NoRouteFound):
        provider.get_routes(origin, destination)


@respx.mock
def test_tomtom_no_route_found_400_response(
    tomtom_no_route_data: dict[str, Any], mock_client: httpx.Client
) -> None:
    origin = Coordinate(lat=21.3069, lon=-157.8583)
    destination = Coordinate(lat=32.7767, lon=-96.7970)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/21.3069,-157.8583:32.7767,-96.797/json"
    ).mock(return_value=httpx.Response(400, json=tomtom_no_route_data))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(NoRouteFound) as exc_info:
        provider.get_routes(origin, destination)

    assert "no route found" in str(exc_info.value).lower()


@respx.mock
def test_tomtom_other_400_error_response(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(400, json={"error": "Bad Request: invalid coordinate"}))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(ProviderBadResponse):
        provider.get_routes(origin, destination)


@respx.mock
def test_tomtom_malformed_error_body(mock_client: httpx.Client) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(400, text="not-json"))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(ProviderBadResponse):
        provider.get_routes(origin, destination)


# ---------------------------------------------------------------------------
# Secret leak & logging security test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "failure_mode",
    ["timeout", "rate_limited", "auth_failed", "server_error", "bad_response", "no_route"],
)
@respx.mock
def test_secret_key_never_leaked_in_exceptions_or_logs(
    failure_mode: str,
    caplog: pytest.LogCaptureFixture,
    tomtom_no_route_data: dict[str, Any],
    mock_client: httpx.Client,
) -> None:
    secret_key = "SECRETKEY123"
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    route_mock = respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    )

    if failure_mode == "timeout":
        route_mock.mock(side_effect=httpx.ReadTimeout("Timeout"))
    elif failure_mode == "rate_limited":
        route_mock.mock(return_value=httpx.Response(429, text="Rate Limited"))
    elif failure_mode == "auth_failed":
        route_mock.mock(return_value=httpx.Response(401, text="Unauthorized"))
    elif failure_mode == "server_error":
        route_mock.mock(return_value=httpx.Response(500, text="Server Error"))
    elif failure_mode == "bad_response":
        route_mock.mock(return_value=httpx.Response(200, text="bad-json"))
    elif failure_mode == "no_route":
        route_mock.mock(return_value=httpx.Response(400, json=tomtom_no_route_data))

    provider = TomTomRoutingProvider(secret_key, client=mock_client, sleep=lambda _: None)

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ProviderError) as exc_info:
            provider.get_routes(origin, destination)

    exc_text = str(exc_info.value)
    assert secret_key not in exc_text
    assert "https://" not in exc_text
    assert secret_key not in caplog.text


def test_tomtom_init_validation() -> None:
    with pytest.raises(ValueError, match="api_key cannot be empty"):
        TomTomRoutingProvider("")
    with pytest.raises(ValueError, match="api_key cannot be empty"):
        TomTomRoutingProvider("   ")


# ---------------------------------------------------------------------------
# Protocols and Fakes validation
# ---------------------------------------------------------------------------


def test_provider_base_protocols_and_errors() -> None:
    assert issubclass(ProviderTimeout, ProviderError)
    assert issubclass(ProviderRateLimited, ProviderError)
    assert issubclass(ProviderBadResponse, ProviderError)
    assert issubclass(ProviderUnavailable, ProviderError)
    assert issubclass(NoRouteFound, ProviderError)

    # Instantiate protocol dummy stubs to verify signatures and ensure 100% coverage
    assert RoutingProvider.get_routes(None, Coordinate(0, 0), Coordinate(1, 1)) is None
    assert GeocodingProvider.search(None, "test") is None
    assert WeatherProvider.get_series(None, ()) is None
    assert WeatherProvider.get_timezone(None, Coordinate(0, 0)) is None
    assert Cache.get(None, "k") is None
    assert Cache.set(None, "k", "v", 60) is None


def test_fakes_suite() -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    dest = Coordinate(lat=39.7392, lon=-104.9903)
    dummy_route = RawRoute(
        provider_id="fake_1",
        polyline=(origin, dest),
        distance_miles=100.0,
        duration_seconds=3600.0,
        timeline=Timeline.from_points([(0.0, 0.0), (100.0, 3600.0)]),
    )

    # FakeRoutingProvider
    fake_routing = FakeRoutingProvider(routes=[dummy_route])
    routes = fake_routing.get_routes(origin, dest)
    assert len(routes) == 1
    assert fake_routing.calls[0]["origin"] == origin

    err_routing = FakeRoutingProvider(error=ProviderTimeout("timeout"))
    with pytest.raises(ProviderTimeout):
        err_routing.get_routes(origin, dest)

    # FakeGeocodingProvider
    place = Place(label="Dallas, TX", coordinate=origin)
    fake_geo = FakeGeocodingProvider(places_by_query={"Dallas": [place]})
    places = fake_geo.search("Dallas")
    assert places == [place]
    err_geo = FakeGeocodingProvider(error=ProviderUnavailable("down"))
    with pytest.raises(ProviderUnavailable):
        err_geo.search("Dallas")

    # FakeWeatherProvider
    fake_weather = FakeWeatherProvider()
    tz = fake_weather.get_timezone(origin)
    assert tz == "America/Chicago"
    series = fake_weather.get_series([GridCell(lat=32.8, lon=-96.8)])
    assert series == {}
    err_weather = FakeWeatherProvider(error=ProviderRateLimited("rate limit"))
    with pytest.raises(ProviderRateLimited):
        err_weather.get_timezone(origin)
    with pytest.raises(ProviderRateLimited):
        err_weather.get_series([])

    # FakeCache
    cache = FakeCache()
    assert cache.get("k") is None
    cache.set("k", "v", ttl_seconds=60)
    assert cache.get("k") == "v"
    cache.delete("k")
    assert cache.get("k") is None
    cache.set("k2", "v2", ttl_seconds=60)
    cache.clear()
    assert cache.get("k2") is None


# ---------------------------------------------------------------------------
# Types additions validation (Place, GridCell, RawRoute)
# ---------------------------------------------------------------------------


def test_place_validation() -> None:
    coord = Coordinate(lat=32.0, lon=-96.0)
    p = Place(label="City", coordinate=coord)
    assert p.label == "City"

    with pytest.raises(ValueError, match="label cannot be empty"):
        Place(label="", coordinate=coord)
    with pytest.raises(ValueError, match="label cannot be empty"):
        Place(label="   ", coordinate=coord)


def test_grid_cell_validation() -> None:
    cell = GridCell(lat=32.8, lon=-96.8)
    assert cell.lat == 32.8
    assert cell.lon == -96.8

    with pytest.raises(ValueError, match="lat must be between -90 and 90"):
        GridCell(lat=91.0, lon=0.0)
    with pytest.raises(ValueError, match="lon must be between -180 and 180"):
        GridCell(lat=0.0, lon=181.0)
    with pytest.raises(ValueError, match="lat must be between -90 and 90"):
        GridCell(lat=float("nan"), lon=0.0)
    with pytest.raises(ValueError, match="lon must be between -180 and 180"):
        GridCell(lat=0.0, lon=float("inf"))


def test_raw_route_validation() -> None:
    c1 = Coordinate(lat=0.0, lon=0.0)
    c2 = Coordinate(lat=1.0, lon=1.0)
    tl = Timeline.from_points([(0.0, 0.0), (10.0, 600.0)])

    r = RawRoute(
        provider_id="tomtom_0",
        polyline=(c1, c2),
        distance_miles=10.0,
        duration_seconds=600.0,
        timeline=tl,
    )
    assert r.provider_id == "tomtom_0"
    assert r.polyline == (c1, c2)

    with pytest.raises(ValueError, match="provider_id cannot be empty"):
        RawRoute("", (c1, c2), 10.0, 600.0, tl)

    with pytest.raises(ValueError, match="polyline must contain at least 2 points"):
        RawRoute("id", (c1,), 10.0, 600.0, tl)

    with pytest.raises(ValueError, match="distance_miles must be a positive finite"):
        RawRoute("id", (c1, c2), 0.0, 600.0, tl)

    with pytest.raises(ValueError, match="distance_miles must be a positive finite"):
        RawRoute("id", (c1, c2), -5.0, 600.0, tl)

    with pytest.raises(ValueError, match="distance_miles must be a positive finite"):
        RawRoute("id", (c1, c2), float("nan"), 600.0, tl)

    with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
        RawRoute("id", (c1, c2), 10.0, -1.0, tl)

    with pytest.raises(ValueError, match="duration_seconds must be non-negative"):
        RawRoute("id", (c1, c2), 10.0, float("inf"), tl)


# ---------------------------------------------------------------------------
# Default client & additional coverage tests
# ---------------------------------------------------------------------------


@respx.mock
def test_tomtom_default_client_execution(tomtom_via_route_data: dict[str, Any]) -> None:
    """Verifies that client=None initializes an internal httpx.Client correctly."""
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)

    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=tomtom_via_route_data))

    provider = TomTomRoutingProvider("test_key", client=None, sleep=lambda _: None)
    routes = provider.get_routes(origin, destination)
    assert len(routes) == 1


@respx.mock
def test_tomtom_route_without_guidance_instructions_builds_two_point_timeline(
    mock_client: httpx.Client,
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)
    payload = {
        "routes": [
            {
                "summary": {"lengthInMeters": 16093.44, "travelTimeInSeconds": 3600},
                "legs": [
                    {
                        "points": [
                            {"latitude": 32.7767, "longitude": -96.7970},
                            {"latitude": 39.7392, "longitude": -104.9903},
                        ]
                    }
                ],
                "guidance": {"instructions": "not_a_list"},
            }
        ]
    }
    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=payload))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    routes = provider.get_routes(origin, destination)
    assert len(routes) == 1
    assert len(routes[0].timeline.distances_miles) == 2


@respx.mock
def test_tomtom_route_with_instructions_ending_at_total_distance(
    mock_client: httpx.Client,
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)
    payload = {
        "routes": [
            {
                "summary": {"lengthInMeters": 16093.44, "travelTimeInSeconds": 3600},
                "legs": [
                    {
                        "points": [
                            {"latitude": 32.7767, "longitude": -96.7970},
                            {"latitude": 39.7392, "longitude": -104.9903},
                        ]
                    }
                ],
                "guidance": {
                    "instructions": [
                        {"routeOffsetInMeters": 0, "travelTimeInSeconds": 0},
                        {"routeOffsetInMeters": 16093.44, "travelTimeInSeconds": 3590},
                    ]
                },
            }
        ]
    }
    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=payload))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    routes = provider.get_routes(origin, destination)
    assert len(routes) == 1
    assert routes[0].timeline.distances_miles[-1] == 10.0
    assert routes[0].timeline.elapsed_seconds[-1] == 3600.0


@respx.mock
def test_tomtom_route_with_single_point_polyline_raises_bad_response(
    mock_client: httpx.Client,
) -> None:
    origin = Coordinate(lat=32.7767, lon=-96.7970)
    destination = Coordinate(lat=39.7392, lon=-104.9903)
    payload = {
        "routes": [
            {
                "summary": {"lengthInMeters": 100, "travelTimeInSeconds": 10},
                "legs": [{"points": [{"latitude": 32.7767, "longitude": -96.7970}]}],
            }
        ]
    }
    respx.get(
        url__startswith="https://api.tomtom.com/routing/1/calculateRoute/32.7767,-96.797:39.7392,-104.9903/json"
    ).mock(return_value=httpx.Response(200, json=payload))

    provider = TomTomRoutingProvider("test_key", client=mock_client, sleep=lambda _: None)
    with pytest.raises(ProviderBadResponse, match="fewer than 2 coordinates"):
        provider.get_routes(origin, destination)


def test_is_no_route_error_with_non_dict() -> None:
    from core.providers.routing_tomtom import _is_no_route_error

    assert _is_no_route_error("string_error") is False
    assert _is_no_route_error(None) is False


def test_raw_route_with_list_polyline_converts_to_tuple() -> None:
    c1 = Coordinate(lat=0.0, lon=0.0)
    c2 = Coordinate(lat=1.0, lon=1.0)
    tl = Timeline.from_points([(0.0, 0.0), (10.0, 600.0)])
    r = RawRoute(
        provider_id="tomtom_0",
        polyline=[c1, c2],  # list passed
        distance_miles=10.0,
        duration_seconds=600.0,
        timeline=tl,
    )
    assert isinstance(r.polyline, tuple)
