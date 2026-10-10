"""Unit tests for RouteSelectionService."""

import pytest

from core.domain.types import Coordinate, RawRoute, Timeline
from core.providers.base import NoRouteFound, ProviderTimeout, ProviderUnavailable
from core.services.route_selection import RouteSelectionService
from core.tests.fakes import FakeCache, FakeRoutingProvider


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


@pytest.fixture
def test_coords() -> tuple[Coordinate, Coordinate]:
    origin = Coordinate(32.7767, -96.7970)
    dest = Coordinate(39.7392, -104.9903)
    return origin, dest


@pytest.fixture
def synthetic_routes(
    test_coords: tuple[Coordinate, Coordinate],
) -> tuple[RawRoute, RawRoute, RawRoute]:
    origin, dest = test_coords
    mid_direct = Coordinate(36.25, -100.89)
    mid_west = Coordinate(36.25, -103.50)
    mid_east = Coordinate(36.25, -98.00)

    r1 = _make_route("native_1", (origin, mid_direct, dest), 660.0, 36000.0)
    r2 = _make_route("native_2", (origin, mid_west, dest), 710.0, 38500.0)
    r3 = _make_route("native_3", (origin, mid_east, dest), 720.0, 39500.0)
    return r1, r2, r3


def test_three_native_routes_cause_no_via_calls(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    origin, dest = test_coords
    r1, r2, r3 = synthetic_routes
    provider = FakeRoutingProvider(routes=[r1, r2, r3])
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    selection = service.get_routes(origin, dest)

    assert len(selection.routes) == 3
    assert len(selection.warnings) == 0
    # Exactly one native provider call, zero via calls
    assert len(provider.calls) == 1
    assert provider.calls[0]["via"] == ()
    assert [r.route_id for r in selection.routes] == ["route_a", "route_b", "route_c"]
    assert [r.label for r in selection.routes] == ["Route A", "Route B", "Route C"]


def test_two_native_routes_cause_four_via_calls_and_picks_lowest_overlap(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    origin, dest = test_coords
    r1, r2, _ = synthetic_routes

    # Script via routes with differing overlaps and durations
    # Via route high overlap (nearly follows r1)
    via_high_overlap = _make_route(
        "via_high",
        (origin, Coordinate(36.25, -100.90), dest),
        665.0,
        37000.0,
    )
    # Via route low overlap (distinct path)
    via_low_overlap = _make_route(
        "via_low",
        (origin, Coordinate(36.25, -97.50), dest),
        730.0,
        39000.0,
    )

    def via_route_fn(pt: Coordinate) -> list[RawRoute]:
        if pt.lon > -100.0:
            return [via_low_overlap]
        return [via_high_overlap]

    provider = FakeRoutingProvider(
        routes=[r1, r2],
        via_route_fn=via_route_fn,
    )
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    selection = service.get_routes(origin, dest)

    # 1 native call + 4 via calls = 5 provider calls
    assert len(provider.calls) == 5
    via_calls = [c for c in provider.calls if len(c["via"]) > 0]
    assert len(via_calls) == 4

    assert len(selection.routes) == 3
    assert len(selection.warnings) == 0

    # Routes must be sorted ascending by duration
    durations = [r.raw.duration_seconds for r in selection.routes]
    assert durations == sorted(durations)
    assert selection.routes[0].route_id == "route_a"
    assert selection.routes[1].route_id == "route_b"
    assert selection.routes[2].route_id == "route_c"
    # The low-overlap via route should be selected
    raw_ids = [r.raw.provider_id for r in selection.routes]
    assert "via_low" in raw_ids


def test_all_via_calls_fail_gives_two_routes_plus_warning(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    origin, dest = test_coords
    r1, r2, _ = synthetic_routes
    provider = FakeRoutingProvider(
        routes=[r1, r2],
        via_error=ProviderUnavailable("Via upstream down"),
    )
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    # Via failures must not raise; returns remaining routes plus warning
    selection = service.get_routes(origin, dest)

    assert len(selection.routes) == 2
    assert len(selection.warnings) == 1
    assert selection.warnings[0].code == "FEWER_THAN_3_ROUTES"
    assert selection.routes[0].route_id == "route_a"
    assert selection.routes[1].route_id == "route_b"


def test_one_native_route_plus_vias(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    origin, dest = test_coords
    r1, _, _ = synthetic_routes
    via_route_1 = _make_route("via_1", (origin, Coordinate(36.0, -103.0), dest), 710.0, 38000.0)
    via_route_2 = _make_route("via_2", (origin, Coordinate(36.0, -98.0), dest), 720.0, 39000.0)

    def via_route_fn(pt: Coordinate) -> list[RawRoute]:
        if pt.lon > -100.0:
            return [via_route_2]
        return [via_route_1]

    provider = FakeRoutingProvider(
        routes=[r1],
        via_route_fn=via_route_fn,
    )
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    selection = service.get_routes(origin, dest)

    assert len(selection.routes) == 3
    assert len(selection.warnings) == 0
    assert len(provider.calls) == 5


def test_native_no_route_found_propagates(test_coords: tuple[Coordinate, Coordinate]) -> None:
    origin, dest = test_coords
    provider = FakeRoutingProvider(error=NoRouteFound("No route between points"))
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    with pytest.raises(NoRouteFound, match="No route between points"):
        service.get_routes(origin, dest)


def test_native_provider_timeout_propagates(test_coords: tuple[Coordinate, Coordinate]) -> None:
    origin, dest = test_coords
    provider = FakeRoutingProvider(error=ProviderTimeout("Timed out"))
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    with pytest.raises(ProviderTimeout, match="Timed out"):
        service.get_routes(origin, dest)


def test_second_call_hits_cache(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    origin, dest = test_coords
    r1, r2, r3 = synthetic_routes
    provider = FakeRoutingProvider(routes=[r1, r2, r3])
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    first_selection = service.get_routes(origin, dest)
    assert len(provider.calls) == 1

    # Second call with the same inputs
    second_selection = service.get_routes(origin, dest)
    # Provider call count remains unchanged
    assert len(provider.calls) == 1
    assert first_selection == second_selection


def test_via_failures_never_raise(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    origin, dest = test_coords
    r1, r2, _ = synthetic_routes
    # Provider raises unexpected RuntimeError on via calls
    provider = FakeRoutingProvider(
        routes=[r1, r2],
        via_error=ProviderTimeout("Via timed out"),
    )
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)

    # Must complete safely without raising
    selection = service.get_routes(origin, dest)
    assert len(selection.routes) == 2
    assert len(selection.warnings) == 1


def test_custom_executor_support(
    test_coords: tuple[Coordinate, Coordinate],
    synthetic_routes: tuple[RawRoute, RawRoute, RawRoute],
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    origin, dest = test_coords
    r1, r2, _ = synthetic_routes
    via_low = _make_route("via_low", (origin, Coordinate(36.25, -97.50), dest), 730.0, 39000.0)

    provider = FakeRoutingProvider(routes=[r1, r2], via_routes=[via_low])
    cache = FakeCache()
    with ThreadPoolExecutor(max_workers=2) as custom_executor:
        service = RouteSelectionService(
            provider=provider,
            cache=cache,
            ttl_seconds=1800,
            executor=custom_executor,
        )
        selection = service.get_routes(origin, dest)
        assert len(selection.routes) == 3


def test_zero_length_segments_in_route_polyline(test_coords: tuple[Coordinate, Coordinate]) -> None:
    origin, dest = test_coords
    mid = Coordinate(36.25, -100.89)
    # Consecutive identical points in polyline
    route_with_dups = _make_route("r_dups", (origin, mid, mid, mid, dest), 660.0, 36000.0)

    provider = FakeRoutingProvider(routes=[route_with_dups])
    cache = FakeCache()
    service = RouteSelectionService(provider=provider, cache=cache, ttl_seconds=1800)
    selection = service.get_routes(origin, dest)
    assert len(selection.routes) >= 1
