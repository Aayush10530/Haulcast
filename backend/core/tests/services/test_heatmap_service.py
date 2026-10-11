"""Unit tests for HeatmapService orchestrator."""

import datetime
from collections.abc import Sequence

import pytest

from core.domain.errors import BeyondForecastHorizonError, DepartureOutOfWindowError
from core.domain.types import (
    Coordinate,
    GridCell,
    HourlySeries,
    IntervalMode,
    Place,
    RawRoute,
    Timeline,
    TripRequest,
    WeatherSeries,
)
from core.services.heatmap_service import HeatmapService
from core.services.route_selection import RouteSelectionService
from core.tests.fakes import FakeCache, FakeRoutingProvider, FakeWeatherProvider


def _make_route(
    route_id: str,
    polyline: tuple[Coordinate, ...],
    distance_miles: float,
    duration_seconds: float,
) -> RawRoute:
    timeline = Timeline.from_points([(0.0, 0.0), (distance_miles, duration_seconds)])
    return RawRoute(
        provider_id=route_id,
        polyline=polyline,
        distance_miles=distance_miles,
        duration_seconds=duration_seconds,
        timeline=timeline,
    )


def _make_series(start_epoch: int, count: int = 72) -> WeatherSeries:
    w = HourlySeries(start_epoch=start_epoch, values=tuple(15.0 for _ in range(count)))
    r = HourlySeries(start_epoch=start_epoch, values=tuple(0.0 for _ in range(count)))
    s = HourlySeries(start_epoch=start_epoch, values=tuple(0.0 for _ in range(count)))
    return WeatherSeries(tz_name="America/Chicago", wind_mph=w, rain_in_hr=r, snow_in_hr=s)


class TrackingWeatherProvider(FakeWeatherProvider):
    def __init__(self, tz_name: str = "America/Chicago") -> None:
        super().__init__(timezone=tz_name)
        self.call_count = 0
        self.series_override: dict[GridCell, WeatherSeries] | None = None

    def get_series(self, cells: Sequence[GridCell]) -> dict[GridCell, WeatherSeries]:
        self.call_count += 1
        if self.series_override is not None:
            return {c: self.series_override[c] for c in cells if c in self.series_override}
        # Default generous series
        now_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
        series = _make_series(now_epoch, count=72)
        return {c: series for c in cells}


@pytest.fixture
def fixed_now() -> datetime.datetime:
    return datetime.datetime(2026, 10, 12, 12, 0, 0, tzinfo=datetime.UTC)


def test_heatmap_service_calls_weather_once_and_builds_result(fixed_now: datetime.datetime) -> None:
    p_orig = Place("Dallas, TX", Coordinate(32.7767, -96.7970))
    p_dest = Place("Denver, CO", Coordinate(39.7392, -104.9903))
    r1 = _make_route(
        "r1", (p_orig.coordinate, Coordinate(35.0, -100.0), p_dest.coordinate), 100.0, 7200.0
    )

    routing = FakeRoutingProvider(routes=[r1])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)
    weather = TrackingWeatherProvider()

    service = HeatmapService(
        route_selection=route_service, weather=weather, clock=lambda: fixed_now
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=42000,
        interval_mode=IntervalMode.AUTO,
    )

    result = service.build(req)

    # Weather provider called exactly once
    assert weather.call_count == 1
    assert result.origin_tz == "America/Chicago"
    assert "2026-10-12" in result.start_local
    assert len(result.heatmap.frames) == 49
    assert len(result.frame_times_local) == 49
    assert len(result.heatmap.cells) > 0


def test_heatmap_service_reuses_cached_routes(fixed_now: datetime.datetime) -> None:
    p_orig = Place("Dallas, TX", Coordinate(32.7767, -96.7970))
    p_dest = Place("Denver, CO", Coordinate(39.7392, -104.9903))
    r1 = _make_route(
        "r1", (p_orig.coordinate, Coordinate(35.0, -100.0), p_dest.coordinate), 100.0, 7200.0
    )

    class TrackingRouting(FakeRoutingProvider):
        def __init__(self, routes):
            super().__init__(routes=routes)
            self.route_calls = 0

        def get_routes(self, origin, destination, via=(), max_routes=3):
            self.route_calls += 1
            return super().get_routes(origin, destination, via=via, max_routes=max_routes)

    routing = TrackingRouting(routes=[r1])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)
    weather = TrackingWeatherProvider()

    # Pre-warm route cache (as would happen in POST /api/trips/analyze/)
    route_service.get_routes(p_orig.coordinate, p_dest.coordinate)
    initial_calls = routing.route_calls
    assert initial_calls > 0

    service = HeatmapService(
        route_selection=route_service, weather=weather, clock=lambda: fixed_now
    )
    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=42000,
        interval_mode=IntervalMode.AUTO,
    )

    service.build(req)
    # Routing was NOT called again; it reused cached routes
    assert routing.route_calls == initial_calls


def test_heatmap_service_departure_window_errors_identical_to_analyze(
    fixed_now: datetime.datetime,
) -> None:
    p_orig = Place("Dallas, TX", Coordinate(32.7767, -96.7970))
    p_dest = Place("Denver, CO", Coordinate(39.7392, -104.9903))
    r1 = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 100.0, 7200.0)

    routing = FakeRoutingProvider(routes=[r1])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)
    weather = TrackingWeatherProvider()
    service = HeatmapService(
        route_selection=route_service, weather=weather, clock=lambda: fixed_now
    )

    # 1. Past departure (> 1 hour in the past)
    past_req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 11, 8, 0, 0),
        load_weight_lb=42000,
        interval_mode=IntervalMode.AUTO,
    )
    with pytest.raises(DepartureOutOfWindowError):
        service.build(past_req)

    # 2. Distant future departure (> 7 days)
    future_req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 25, 8, 0, 0),
        load_weight_lb=42000,
        interval_mode=IntervalMode.AUTO,
    )
    with pytest.raises(DepartureOutOfWindowError):
        service.build(future_req)


def test_heatmap_service_raises_beyond_horizon_when_frame_zero_is_all_none(
    fixed_now: datetime.datetime,
) -> None:
    p_orig = Place("Dallas, TX", Coordinate(32.7767, -96.7970))
    p_dest = Place("Denver, CO", Coordinate(39.7392, -104.9903))
    r1 = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 100.0, 7200.0)

    routing = FakeRoutingProvider(routes=[r1])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)
    weather = TrackingWeatherProvider()
    # Empty series override -> all cells have no weather
    weather.series_override = {}

    service = HeatmapService(
        route_selection=route_service, weather=weather, clock=lambda: fixed_now
    )
    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=42000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(BeyondForecastHorizonError, match="Forecast data unavailable"):
        service.build(req)
