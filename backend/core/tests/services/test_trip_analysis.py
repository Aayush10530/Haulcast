"""Unit tests for TripAnalysisService orchestrator (F-025)."""

import datetime

import pytest

from core.domain import geometry
from core.domain.errors import (
    BeyondForecastHorizonError,
    DepartureOutOfWindowError,
    NonexistentLocalTimeError,
)
from core.domain.grid import snap_to_cell
from core.domain.types import (
    Coordinate,
    HourlySeries,
    IntervalMode,
    Place,
    RawRoute,
    RiskDriver,
    RiskLevel,
    Timeline,
    TripRequest,
    WeatherSeries,
)
from core.providers.base import ProviderBadResponse
from core.services.route_selection import RouteSelectionService
from core.services.trip_analysis import TripAnalysisService
from core.tests.fakes import FakeCache, FakeRoutingProvider, FakeWeatherProvider


def _make_route(
    route_id: str,
    polyline: tuple[Coordinate, ...],
    distance_miles: float,
    duration_seconds: float,
    timeline_override: Timeline | None = None,
) -> RawRoute:
    timeline = timeline_override or Timeline.from_points(
        [(0.0, 0.0), (distance_miles, duration_seconds)]
    )
    return RawRoute(
        provider_id=route_id,
        polyline=polyline,
        distance_miles=distance_miles,
        duration_seconds=duration_seconds,
        timeline=timeline,
    )


def _make_series(
    start_epoch: int,
    count: int = 48,
    wind: float | None = 10.0,
    rain: float | None = 0.0,
    snow: float | None = 0.0,
    tz_name: str = "America/Chicago",
) -> WeatherSeries:
    w = HourlySeries(start_epoch=start_epoch, values=tuple(wind for _ in range(count)))
    r = HourlySeries(start_epoch=start_epoch, values=tuple(rain for _ in range(count)))
    s = HourlySeries(start_epoch=start_epoch, values=tuple(snow for _ in range(count)))
    return WeatherSeries(tz_name=tz_name, wind_mph=w, rain_in_hr=r, snow_in_hr=s)


@pytest.fixture
def fixed_now() -> datetime.datetime:
    return datetime.datetime(2026, 10, 12, 12, 0, 0, tzinfo=datetime.UTC)


@pytest.fixture
def test_places() -> tuple[Place, Place]:
    p1 = Place("Dallas, TX", Coordinate(32.7767, -96.7970))
    p2 = Place("Denver, CO", Coordinate(39.7392, -104.9903))
    return p1, p2


def test_normal_three_route_analysis_end_to_end(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    # Route 1: 100 mi, 7200s (Fastest, duration 2h)
    # Route 2: 120 mi, 7500s (Safest)
    # Route 3: 130 mi, 8000s
    c_mid1 = Coordinate(33.0, -103.0)
    c_mid2 = Coordinate(38.0, -97.0)
    c_mid3 = Coordinate(36.0, -100.0)

    r1 = _make_route("r1", (p_orig.coordinate, c_mid1, p_dest.coordinate), 100.0, 7200.0)
    r2 = _make_route("r2", (p_orig.coordinate, c_mid2, p_dest.coordinate), 120.0, 7500.0)
    r3 = _make_route("r3", (p_orig.coordinate, c_mid3, p_dest.coordinate), 130.0, 8000.0)

    routing = FakeRoutingProvider(routes=[r1, r2, r3])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)

    # Departure 1 hour from now: 2026-10-12 08:00 local
    # (in America/Chicago CDT is UTC-5 -> 13:00 UTC)
    dep_local = datetime.datetime(2026, 10, 12, 8, 0, 0)
    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())

    # Build weather: Route A has 1 Severe checkpoint (10 mi); Route C has 2 (20 mi); Route B has Low
    cum1 = geometry.cumulative_miles(r1.polyline, r1.distance_miles)
    pt_severe = geometry.point_at_mile(r1.polyline, cum1, 50.0)
    cell_severe = snap_to_cell(pt_severe)

    cum3 = geometry.cumulative_miles(r3.polyline, r3.distance_miles)
    pt_severe3a = geometry.point_at_mile(r3.polyline, cum3, 40.0)
    cell_severe3a = snap_to_cell(pt_severe3a)
    pt_severe3b = geometry.point_at_mile(r3.polyline, cum3, 50.0)
    cell_severe3b = snap_to_cell(pt_severe3b)

    weather_map = {
        cell_severe: _make_series(start_epoch, count=24, wind=50.0),
        cell_severe3a: _make_series(start_epoch, count=24, wind=50.0),
        cell_severe3b: _make_series(start_epoch, count=24, wind=50.0),
    }

    class SyntheticWeather(FakeWeatherProvider):
        def get_series(self, cells):
            super().get_series(cells)
            res = {}
            for c in cells:
                if c in weather_map:
                    res[c] = weather_map[c]
                else:
                    res[c] = _make_series(start_epoch, count=24, wind=10.0)
            return res

    weather = SyntheticWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=dep_local,
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    analysis = service.analyze(req)

    # 130 mi <= 250 mi -> AUTO interval = 10 mi
    assert analysis.request.interval_miles == 10
    assert analysis.request.departure_utc == datetime.datetime(
        2026, 10, 12, 13, 0, 0, tzinfo=datetime.UTC
    )
    assert analysis.request.origin_tz == "America/Chicago"

    assert len(analysis.routes) == 3
    # Check Route A (100 mi): 11 checkpoints (0, 10, ..., 100)
    ra = analysis.routes[0]
    assert ra.route_id == "route_a"
    assert len(ra.checkpoints) == 11
    assert ra.checkpoints[0].eta_utc == datetime.datetime(
        2026, 10, 12, 13, 0, 0, tzinfo=datetime.UTC
    )
    assert ra.checkpoints[-1].eta_utc == datetime.datetime(
        2026, 10, 12, 15, 0, 0, tzinfo=datetime.UTC
    )

    # Route A has severe checkpoint from cell_mid1; Route B has 0 severe miles
    rb = analysis.routes[1]
    assert rb.route_id == "route_b"
    assert rb.summary.miles_by_level.severe == 0.0

    # Recommendation should pick safer Route B over faster Route A
    assert analysis.recommendation.route_id == "route_b"
    assert analysis.recommendation.decided_by.name == "SEVERE_MILES"
    assert rb.is_recommended is True
    assert ra.is_recommended is False
    assert rb.rank == 1
    assert ra.rank == 2

    # Meta
    assert analysis.meta.route_count == 3
    assert analysis.meta.weather_cells > 0
    assert analysis.meta.elapsed_ms >= 0.0


def test_load_rule_flows_through(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 100.0, 7200.0)
    routing = FakeRoutingProvider(routes=[r])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    # 40 mph wind: Table is High, but load 45,000 lb elevates to Severe!
    series = _make_series(start_epoch, count=24, wind=40.0)

    class FixedWeather(FakeWeatherProvider):
        def get_series(self, cells):
            return {c: series for c in cells}

    weather = FixedWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=45000,
        interval_mode=IntervalMode.AUTO,
    )

    analysis = service.analyze(req)
    # Check that load rule elevated checkpoint assessment to Severe
    for cp in analysis.routes[0].checkpoints:
        assert cp.assessment is not None
        assert cp.assessment.level == RiskLevel.SEVERE
        assert cp.assessment.driver == RiskDriver.LOAD_RULE
        assert cp.assessment.load_rule_applied is True


def test_manual_interval_25(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 100.0, 7200.0)
    routing = FakeRoutingProvider(routes=[r])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    weather = FakeWeatherProvider(
        series_by_cell={
            snap_to_cell(p_orig.coordinate): _make_series(start_epoch),
            snap_to_cell(p_dest.coordinate): _make_series(start_epoch),
        }
    )

    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.MANUAL,
        manual_interval=25,
    )

    analysis = service.analyze(req)
    assert analysis.request.interval_miles == 25
    # 100 mi / 25 mi interval -> 5 checkpoints (0, 25, 50, 75, 100)
    assert len(analysis.routes[0].checkpoints) == 5


def test_one_unavailable_cell_gives_unavailable_checkpoint_and_warning(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    routing = FakeRoutingProvider(routes=[r])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    c_orig = snap_to_cell(p_orig.coordinate)
    # Only supply series for origin, destination cell missing!
    weather = FakeWeatherProvider(series_by_cell={c_orig: _make_series(start_epoch)})

    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.MANUAL,
        manual_interval=25,
    )

    analysis = service.analyze(req)
    route = analysis.routes[0]
    assert route.summary.unavailable_checkpoints > 0
    # Must include WEATHER_UNAVAILABLE_SOME warning with count in message
    warn = next((w for w in analysis.warnings if w.code == "WEATHER_UNAVAILABLE_SOME"), None)
    assert warn is not None
    assert str(route.summary.unavailable_checkpoints) in warn.message


def test_all_cells_unavailable_raises_horizon_error(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    routing = FakeRoutingProvider(routes=[r])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)

    # Empty weather map (no cells available)
    weather = FakeWeatherProvider(series_by_cell={})

    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(BeyondForecastHorizonError):
        service.analyze(req)


def test_all_routes_no_travel_adds_no_safe_route_warning(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r1 = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    routing = FakeRoutingProvider(routes=[r1])
    cache = FakeCache()
    route_service = RouteSelectionService(provider=routing, cache=cache, ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    # 60 mph wind -> No Travel everywhere!
    series = _make_series(start_epoch, count=24, wind=60.0)

    class NoTravelWeather(FakeWeatherProvider):
        def get_series(self, cells):
            return {c: series for c in cells}

    weather = NoTravelWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    analysis = service.analyze(req)
    assert analysis.recommendation.no_safe_route is True
    assert any(w.code == "NO_SAFE_ROUTE" for w in analysis.warnings)


def test_departure_outside_window_raises(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    routing = FakeRoutingProvider(routes=[r])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)
    weather = FakeWeatherProvider()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    # 3 hours in the past (grace is 1 hour)
    past_local = datetime.datetime(2026, 10, 12, 4, 0, 0)
    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=past_local,
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(DepartureOutOfWindowError):
        service.analyze(req)


def test_nonexistent_local_time_raises(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    routing = FakeRoutingProvider(routes=[r])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)
    weather = FakeWeatherProvider(timezone="America/Chicago")

    def dst_clock() -> datetime.datetime:
        return datetime.datetime(2026, 3, 7, 12, 0, 0, tzinfo=datetime.UTC)

    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=dst_clock,
    )

    # 2026-03-08 02:30 does not exist in America/Chicago (spring-forward gap 2:00 -> 3:00)
    gap_local = datetime.datetime(2026, 3, 8, 2, 30, 0)
    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=gap_local,
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(NonexistentLocalTimeError):
        service.analyze(req)


def test_timeline_mismatch_raises_provider_bad_response(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    # Timeline ends at 100.5 mi, but route distance is 100.0 mi (diff > 0.01)
    bad_timeline = Timeline.from_points([(0.0, 0.0), (100.5, 7200.0)])
    r = _make_route(
        "r1",
        (p_orig.coordinate, p_dest.coordinate),
        100.0,
        7200.0,
        timeline_override=bad_timeline,
    )
    routing = FakeRoutingProvider(routes=[r])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)
    weather = FakeWeatherProvider()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(ProviderBadResponse, match="timeline total miles"):
        service.analyze(req)


def test_weather_called_exactly_once_with_deduplicated_cells(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    # 2 routes sharing coordinates
    r1 = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    r2 = _make_route("r2", (p_orig.coordinate, p_dest.coordinate), 50.0, 3700.0)
    routing = FakeRoutingProvider(routes=[r1, r2])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    series = _make_series(start_epoch, count=24)

    class TrackingWeather(FakeWeatherProvider):
        def get_series(self, cells):
            super().get_series(cells)
            return {c: series for c in cells}

    weather = TrackingWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    service.analyze(req)
    series_calls = [c for c in weather.calls if "cells" in c]
    assert len(series_calls) == 1
    requested_cells = series_calls[0]["cells"]
    # Verify no duplicates
    assert len(requested_cells) == len(set(requested_cells))


def test_fewer_than_three_routes_carries_warning(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    # Only 2 routes available
    r1 = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 50.0, 3600.0)
    r2 = _make_route("r2", (p_orig.coordinate, p_dest.coordinate), 55.0, 3800.0)
    routing = FakeRoutingProvider(routes=[r1, r2])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    series = _make_series(start_epoch, count=24)

    class WeatherMock(FakeWeatherProvider):
        def get_series(self, cells):
            return {c: series for c in cells}

    weather = WeatherMock()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    analysis = service.analyze(req)
    assert any(w.code == "FEWER_THAN_3_ROUTES" for w in analysis.warnings)


def test_last_checkpoint_eta_precision(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    dist = 100.0
    dur = 7200.0
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), dist, dur)
    routing = FakeRoutingProvider(routes=[r])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)

    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    series = _make_series(start_epoch, count=24)

    class WeatherMock(FakeWeatherProvider):
        def get_series(self, cells):
            return {c: series for c in cells}

    weather = WeatherMock()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    analysis = service.analyze(req)
    last_cp = analysis.routes[0].checkpoints[-1]
    expected_eta = analysis.request.departure_utc + datetime.timedelta(seconds=dur)
    diff_micro = abs((last_cp.eta_utc - expected_eta).total_seconds())
    assert diff_micro < 1e-6


def test_eta_beyond_series_window_raises_horizon_error(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    # 5 hour duration (18000s)
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 250.0, 18000.0)
    routing = FakeRoutingProvider(routes=[r])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)

    # Weather series only covers 2 hours
    start_epoch = int(datetime.datetime(2026, 10, 12, 13, 0, 0, tzinfo=datetime.UTC).timestamp())
    short_series = _make_series(start_epoch, count=2)

    class ShortWeather(FakeWeatherProvider):
        def get_series(self, cells):
            return {c: short_series for c in cells}

    weather = ShortWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(BeyondForecastHorizonError, match="exceeds available forecast horizon"):
        service.analyze(req)


def test_all_checkpoints_missing_weather_sample_raises_horizon_error(
    fixed_now: datetime.datetime,
    test_places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = test_places
    r = _make_route("r1", (p_orig.coordinate, p_dest.coordinate), 100.0, 7200.0)
    routing = FakeRoutingProvider(routes=[r])
    route_service = RouteSelectionService(provider=routing, cache=FakeCache(), ttl_seconds=1800)

    # 24 hours of series, but all values are None -> sample_at returns None
    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())
    none_series = _make_series(start_epoch, count=24, wind=None, rain=None, snow=None)

    class NoneWeather(FakeWeatherProvider):
        def get_series(self, cells):
            return {c: none_series for c in cells}

    weather = NoneWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=30000,
        interval_mode=IntervalMode.AUTO,
    )

    with pytest.raises(BeyondForecastHorizonError, match="All weather cells unavailable"):
        service.analyze(req)


def test_analyze_zero_load_weight_success(test_places: tuple[Place, Place]) -> None:
    fixed_now = datetime.datetime(2026, 10, 11, 12, 0, 0, tzinfo=datetime.UTC)
    dep_local = datetime.datetime(2026, 10, 12, 8, 0, 0)
    p_orig, p_dest = test_places

    routes = [
        _make_route(
            "raw_a",
            (p_orig.coordinate, Coordinate(35.0, -100.0), p_dest.coordinate),
            100.0,
            7200.0,
        )
    ]
    route_service = RouteSelectionService(
        provider=FakeRoutingProvider(routes=routes),
        cache=FakeCache(),
        ttl_seconds=1800,
    )
    start_epoch = int(datetime.datetime(2026, 10, 12, 10, 0, 0, tzinfo=datetime.UTC).timestamp())

    class CalmWeather(FakeWeatherProvider):
        def get_series(self, cells):
            super().get_series(cells)
            return {c: _make_series(start_epoch, count=24, wind=10.0) for c in cells}

    weather = CalmWeather()
    service = TripAnalysisService(
        route_selection=route_service,
        weather=weather,
        clock=lambda: fixed_now,
    )

    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=dep_local,
        load_weight_lb=0,
        interval_mode=IntervalMode.AUTO,
    )

    analysis = service.analyze(req)
    assert analysis.request.load_weight_lb == 0
