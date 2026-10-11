"""Comprehensive API tests for Haulcast endpoints, error envelopes, and validation."""

import datetime
from collections.abc import Generator
from typing import Any

import pytest
from rest_framework.test import APIClient

from api.container import Container, set_container
from core.domain.errors import (
    BeyondForecastHorizonError,
    DepartureOutOfWindowError,
    NonexistentLocalTimeError,
)
from core.domain.grid import snap_to_cell
from core.domain.types import (
    Coordinate,
    HourlySeries,
    Place,
    RawRoute,
    Timeline,
    WeatherSample,
    WeatherSeries,
)
from core.infra.cache import InMemoryTTLCache
from core.providers.base import (
    NoRouteFound,
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from core.services.route_selection import RouteSelectionService
from core.services.trip_analysis import TripAnalysisService
from core.tests.fakes import (
    FakeGeocodingProvider,
    FakeRoutingProvider,
    FakeWeatherProvider,
)

FIXED_NOW = datetime.datetime(2026, 10, 11, 12, 0, tzinfo=datetime.UTC)


def _make_sample(wind: float = 10.0, rain: float = 0.0, snow: float = 0.0) -> WeatherSample:
    return WeatherSample(
        wind_speed_mph=wind,
        rain_rate_in_hr=rain,
        snow_rate_in_hr=snow,
        interpolated_wind=True,
    )


def _make_series(tz_name: str = "America/Chicago") -> WeatherSeries:
    start = int(FIXED_NOW.timestamp()) - 3600
    w = HourlySeries(start_epoch=start, values=tuple(15.0 for _ in range(48)))
    r = HourlySeries(start_epoch=start, values=tuple(0.0 for _ in range(48)))
    s = HourlySeries(start_epoch=start, values=tuple(0.0 for _ in range(48)))
    return WeatherSeries(tz_name=tz_name, wind_mph=w, rain_in_hr=r, snow_in_hr=s)


@pytest.fixture
def api_test_context() -> Generator[dict[str, Any]]:
    cache = InMemoryTTLCache()

    p1 = Coordinate(32.7767, -96.7970)
    p2 = Coordinate(39.7392, -104.9903)
    raw_route = RawRoute(
        provider_id="tomtom_0",
        polyline=(p1, Coordinate(35.0, -100.0), p2),
        distance_miles=100.0,
        duration_seconds=7200.0,
        timeline=Timeline.from_points(((0.0, 0.0), (100.0, 7200.0))),
        via_summary="I-35 N",
    )

    routing = FakeRoutingProvider(routes=[raw_route])

    cell1 = snap_to_cell(p1)
    cell2 = snap_to_cell(p2)
    series_map = {
        cell1: _make_series("America/Chicago"),
        cell2: _make_series("America/Denver"),
    }
    weather = FakeWeatherProvider(series_by_cell=series_map, timezone="America/Chicago")

    geocoding = FakeGeocodingProvider(
        places_by_query={
            "Dallas": [
                Place("Dallas, TX", p1, id="1"),
                Place("Dallas Fort Worth", Coordinate(32.8998, -97.0403), id="2"),
            ]
        }
    )

    route_selection = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)
    trip_analysis = TripAnalysisService(
        route_selection=route_selection,
        weather=weather,
        clock=lambda: FIXED_NOW,
    )

    container = Container(
        cache=cache,
        routing=routing,
        weather=weather,
        route_selection=route_selection,
        trip_analysis=trip_analysis,
        geocoding=geocoding,
    )
    set_container(container)

    yield {
        "container": container,
        "routing": routing,
        "weather": weather,
        "geocoding": geocoding,
        "trip_analysis": trip_analysis,
    }

    set_container(None)


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def valid_payload() -> dict[str, Any]:
    return {
        "origin": {"label": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
        "destination": {"label": "Denver, CO", "lat": 39.7392, "lon": -104.9903},
        "departure_local": "2026-10-12T08:00",
        "load_weight_lb": 42000,
        "interval": "auto",
    }


# ============================================================================
# Status Code & Error Envelope Tests
# ============================================================================


def test_status_400_validation_error_missing_and_out_of_range(
    api_test_context: dict[str, Any], client: APIClient
) -> None:
    # 1. Lat/Lon out of range
    res = client.post(
        "/api/trips/analyze/",
        {
            "origin": {"label": "Dallas", "lat": 120.0, "lon": -96.7970},
            "destination": {"label": "Denver", "lat": 39.7392, "lon": -104.9903},
            "departure_local": "2026-10-12T08:00",
            "load_weight_lb": 42000,
        },
        format="json",
    )
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "validation_error"
    assert "origin" in data["error"]["fields"]

    # 2. Origin and destination closer than 0.5 miles
    res2 = client.post(
        "/api/trips/analyze/",
        {
            "origin": {"label": "Dallas 1", "lat": 32.7767, "lon": -96.7970},
            "destination": {"label": "Dallas 2", "lat": 32.7768, "lon": -96.7971},
            "departure_local": "2026-10-12T08:00",
            "load_weight_lb": 42000,
        },
        format="json",
    )
    assert res2.status_code == 400
    data2 = res2.json()
    assert "destination" in data2["error"]["fields"]
    assert "0.5 miles" in data2["error"]["fields"]["destination"][0]

    # 3. Bad interval value
    bad_interval = valid_payload()
    bad_interval["interval"] = "invalid_interval"
    res3 = client.post("/api/trips/analyze/", bad_interval, format="json")
    assert res3.status_code == 400
    assert "interval" in res3.json()["error"]["fields"]

    # 4. Departure with timezone offset rejected
    bad_dep = valid_payload()
    bad_dep["departure_local"] = "2026-10-12T08:00:00+00:00"
    res4 = client.post("/api/trips/analyze/", bad_dep, format="json")
    assert res4.status_code == 400
    assert "departure_local" in res4.json()["error"]["fields"]


def test_status_400_departure_outside_window(
    api_test_context: dict[str, Any], client: APIClient
) -> None:
    # Departure in 2025 (far in the past)
    payload = valid_payload()
    payload["departure_local"] = "2025-01-01T08:00"
    res = client.post("/api/trips/analyze/", payload, format="json")
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "validation_error"
    assert "departure_local" in data["error"]["fields"]
    # Verify origin timezone is included in the error message
    field_msg = data["error"]["fields"]["departure_local"][0]
    assert "America/Chicago" in field_msg


def test_status_400_nonexistent_local_time(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulate NonexistentLocalTimeError from domain
    def fake_analyze(*args: Any, **kwargs: Any) -> Any:
        raise NonexistentLocalTimeError("Local time 2026-03-08 02:30 does not exist due to DST gap")

    ctx = api_test_context["container"]
    monkeypatch.setattr(ctx.trip_analysis, "analyze", fake_analyze)

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 400
    data = res.json()
    assert data["error"]["code"] == "validation_error"
    assert "departure_local" in data["error"]["fields"]


def test_status_422_no_route_found(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(NoRouteFound("No route found")),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "no_route_found"


def test_status_422_beyond_forecast_horizon(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(
            BeyondForecastHorizonError("Times beyond horizon", FIXED_NOW)
        ),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 422
    data = res.json()
    assert data["error"]["code"] == "beyond_forecast_horizon"


def test_status_503_weather_unavailable(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(
            ProviderRateLimited("Weather provider rate limit exceeded")
        ),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 503
    data = res.json()
    assert data["error"]["code"] == "weather_unavailable"


def test_status_503_routing_unavailable(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(
            ProviderUnavailable("Routing provider is currently unavailable")
        ),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 503
    data = res.json()
    assert data["error"]["code"] == "routing_unavailable"


def test_status_504_upstream_timeout(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(ProviderTimeout("Upstream timeout")),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 504
    data = res.json()
    assert data["error"]["code"] == "upstream_timeout"


def test_status_502_upstream_error(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(ProviderBadResponse("Malformed body")),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 502
    data = res.json()
    assert data["error"]["code"] == "upstream_error"


def test_status_500_internal_error_never_shows_traceback(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    ctx = api_test_context["container"]
    monkeypatch.setattr(
        ctx.trip_analysis,
        "analyze",
        lambda req: (_ for _ in ()).throw(RuntimeError("Unexpected internal failure")),
    )

    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 500
    data = res.json()
    assert data["error"]["code"] == "internal_error"
    assert "Traceback" not in res.content.decode()


# ============================================================================
# Endpoint Functionality, Golden Response, Warnings, & Headers
# ============================================================================


def test_successful_analysis_matches_golden_structure(
    api_test_context: dict[str, Any], client: APIClient
) -> None:
    res = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res.status_code == 200
    data = res.json()

    # Verify request echo
    req = data["request"]
    assert req["origin"]["label"] == "Dallas, TX"
    assert req["origin_timezone"] == "America/Chicago"
    assert req["load_weight_lb"] == 42000
    assert req["interval_mode"] == "auto"

    # Verify recommendation
    assert data["recommended_route_id"] == "route_a"
    rec = data["recommendation"]
    assert rec["route_id"] == "route_a"
    assert "decided_by" in rec
    assert "headline" in rec

    # Verify routes
    routes = data["routes"]
    assert len(routes) == 1
    r = routes[0]
    assert r["id"] == "route_a"
    assert "recommended" in r["tags"]
    assert "fastest" in r["tags"]
    assert r["distance_miles"] == 100.0
    assert r["duration_seconds"] == 7200
    assert "arrival_local" in r
    assert len(r["geometry"]) >= 2
    assert isinstance(r["geometry"][0], list)

    # Verify summary
    summ = r["summary"]
    assert "miles_by_level" in summ
    assert "low" in summ["miles_by_level"]
    assert "avg_risk_score" in summ
    assert "max_level" in summ

    # Verify checkpoints
    cps = r["checkpoints"]
    assert len(cps) >= 2
    cp0 = cps[0]
    assert cp0["index"] == 0
    assert cp0["mile"] == 0.0
    assert "eta_utc" in cp0
    assert "eta_local" in cp0
    assert cp0["local_tz"] == "America/Chicago"
    assert cp0["weather"]["wind_mph"] == 15.0

    # Verify meta
    meta = data["meta"]
    assert meta["routing_provider"] == "tomtom"
    assert meta["weather_provider"] == "open-meteo"
    assert "weather_cells" in meta
    assert "elapsed_ms" in meta


def test_load_above_80000_adds_legal_limit_warning(
    api_test_context: dict[str, Any], client: APIClient
) -> None:
    payload = valid_payload()
    payload["load_weight_lb"] = 85000
    res = client.post("/api/trips/analyze/", payload, format="json")
    assert res.status_code == 200
    data = res.json()
    warnings = data["warnings"]
    assert any(w["code"] == "LOAD_ABOVE_LEGAL_LIMIT" for w in warnings)


def test_geocode_validation_and_search(api_test_context: dict[str, Any], client: APIClient) -> None:
    # 1. Too short (< 3 chars)
    res_short = client.get("/api/geocode/?q=Da")
    assert res_short.status_code == 400
    assert "q" in res_short.json()["error"]["fields"]

    # 2. Valid query
    res_ok = client.get("/api/geocode/?q=Dallas")
    assert res_ok.status_code == 200
    places = res_ok.json()
    assert len(places) == 2
    assert places[0]["id"] == "1"
    assert places[0]["label"] == "Dallas, TX"
    assert places[0]["lat"] == 32.7767
    assert places[0]["lon"] == -96.7970


def test_gzip_compression_header(api_test_context: dict[str, Any], client: APIClient) -> None:
    res = client.post(
        "/api/trips/analyze/",
        valid_payload(),
        format="json",
        HTTP_ACCEPT_ENCODING="gzip",
    )
    assert res.status_code == 200
    assert res.headers.get("Content-Encoding") == "gzip"


def test_cors_preflight(client: APIClient) -> None:
    # Allowed origin
    res_allowed = client.options(
        "/api/trips/analyze/",
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert res_allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"

    # Disallowed origin
    res_disallowed = client.options(
        "/api/trips/analyze/",
        HTTP_ORIGIN="http://disallowed-origin.com",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
    )
    assert res_disallowed.headers.get("Access-Control-Allow-Origin") is None


def test_throttling_returns_429_envelope(
    api_test_context: dict[str, Any], client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from django.core.cache import cache
    from rest_framework.settings import api_settings

    from api.throttles import AnalyzeThrottle

    cache.clear()
    monkeypatch.setitem(api_settings.DEFAULT_THROTTLE_RATES, "analyze", "2/min")
    monkeypatch.setitem(AnalyzeThrottle.THROTTLE_RATES, "analyze", "2/min")

    # 1st request ok
    res1 = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res1.status_code == 200

    # 2nd request ok
    res2 = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res2.status_code == 200

    # 3rd request throttled
    res3 = client.post("/api/trips/analyze/", valid_payload(), format="json")
    assert res3.status_code == 429
    data = res3.json()
    assert data["error"]["code"] == "rate_limited"
    assert "Request was throttled" in data["error"]["message"]
    assert "Traceback" not in res3.content.decode()


def test_build_container_and_get_container() -> None:
    from api.container import get_container, set_container

    set_container(None)
    container = get_container()
    assert container is not None
    assert container.routing is not None
    assert container.weather is not None
    assert container.geocoding is not None
    assert container.trip_analysis is not None
    set_container(None)


def test_departure_window_error_without_origin_tz_and_list_validation_errors(
    client: APIClient,
) -> None:
    from rest_framework import exceptions as drf_exc

    from api.errors import custom_exception_handler

    # DepartureOutOfWindowError without origin_tz
    err = DepartureOutOfWindowError(
        "Departure out of window",
        allowed_from=FIXED_NOW,
        allowed_to=FIXED_NOW + datetime.timedelta(days=7),
        origin_tz=None,
    )
    resp = custom_exception_handler(err, {})
    assert resp.status_code == 400
    assert "departure_local" in resp.data["error"]["fields"]

    # ValidationError with list detail
    val_err_list = drf_exc.ValidationError(["Global form error 1", "Global form error 2"])
    resp_list = custom_exception_handler(val_err_list, {})
    assert resp_list.status_code == 400
    assert "non_field_errors" in resp_list.data["error"]["fields"]

    # Other DRF API exception (e.g. MethodNotAllowed)
    mna = drf_exc.MethodNotAllowed("GET")
    resp_mna = custom_exception_handler(mna, {})
    assert resp_mna.status_code == 405
    assert resp_mna.data["error"]["code"] == "method_not_allowed"

    # ValidationError with string detail
    val_err_str = drf_exc.ValidationError("Raw string detail error")
    resp_str = custom_exception_handler(val_err_str, {})
    assert resp_str.status_code == 400
    assert "non_field_errors" in resp_str.data["error"]["fields"]

    # ValidationError with primitive non-list/dict detail
    val_err_prim = drf_exc.ValidationError(12345)
    val_err_prim.detail = 12345  # type: ignore[assignment]
    resp_prim = custom_exception_handler(val_err_prim, {})
    assert resp_prim.status_code == 400
    assert "detail" in resp_prim.data["error"]["fields"]


def test_serializer_edge_cases(client: APIClient, api_test_context: dict[str, Any]) -> None:
    # Unparseable departure date string
    payload = valid_payload()
    payload["departure_local"] = "not-an-iso-datetime"
    res1 = client.post("/api/trips/analyze/", payload, format="json")
    assert res1.status_code == 400
    assert "departure_local" in res1.json()["error"]["fields"]

    # Manual interval choice "25"
    payload2 = valid_payload()
    payload2["interval"] = "25"
    res2 = client.post("/api/trips/analyze/", payload2, format="json")
    assert res2.status_code == 200
    assert res2.json()["request"]["interval_mode"] == "manual"
    assert res2.json()["request"]["interval_miles"] == 25
