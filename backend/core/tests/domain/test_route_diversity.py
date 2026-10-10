"""Unit tests for route diversity analysis and selection."""

import math

import pytest

from core.domain.geometry import haversine_miles
from core.domain.route_diversity import (
    bearing_degrees,
    densify_polyline,
    offset_point,
    select_routes,
    shared_fraction,
)
from core.domain.types import Coordinate, RawRoute, Timeline


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


def test_bearing_degrees_cardinal_directions() -> None:
    p0 = Coordinate(0.0, 0.0)
    p_north = Coordinate(1.0, 0.0)
    p_east = Coordinate(0.0, 1.0)
    p_south = Coordinate(-1.0, 0.0)
    p_west = Coordinate(0.0, -1.0)

    assert math.isclose(bearing_degrees(p0, p_north), 0.0, abs_tol=1e-5)
    assert math.isclose(bearing_degrees(p0, p_east), 90.0, abs_tol=1e-5)
    assert math.isclose(bearing_degrees(p0, p_south), 180.0, abs_tol=1e-5)
    assert math.isclose(bearing_degrees(p0, p_west), 270.0, abs_tol=1e-5)
    assert bearing_degrees(p0, p0) == 0.0


def test_offset_point_north_by_69_09_miles() -> None:
    origin = Coordinate(0.0, 0.0)
    dest = offset_point(origin, bearing_degrees=0.0, miles=69.09)

    # Latitude change should be about 1.0 degree within 0.5%
    delta_lat = dest.lat - origin.lat
    relative_error = abs(delta_lat - 1.0) / 1.0
    assert relative_error < 0.005
    assert math.isclose(dest.lon, 0.0, abs_tol=1e-5)


def test_offset_point_east_west_at_40_degrees() -> None:
    origin = Coordinate(40.0, -100.0)
    east_pt = offset_point(origin, bearing_degrees=90.0, miles=50.0)
    west_pt = offset_point(origin, bearing_degrees=270.0, miles=50.0)

    assert math.isclose(east_pt.lat, 40.0, abs_tol=0.1)
    assert east_pt.lon > origin.lon
    assert math.isclose(west_pt.lat, 40.0, abs_tol=0.1)
    assert west_pt.lon < origin.lon

    # Zero miles returns origin
    assert offset_point(origin, 45.0, 0.0) == origin

    with pytest.raises(ValueError, match="miles must be finite"):
        offset_point(origin, 0.0, float("nan"))


def test_densify_polyline_behaviour() -> None:
    # 1.0 mile segment
    p0 = Coordinate(40.0, -100.0)
    p1 = offset_point(p0, 0.0, 1.0)
    densified = densify_polyline((p0, p1), max_step_miles=0.1)

    assert len(densified) == 11
    assert densified[0] == p0
    assert densified[-1] == p1
    for i in range(1, len(densified)):
        step_dist = haversine_miles(densified[i - 1], densified[i])
        assert step_dist <= 0.1 + 1e-6

    # Segment already shorter than max_step_miles is unchanged
    p_short = offset_point(p0, 0.0, 0.05)
    short_segment = (p0, p_short)
    short_densified = densify_polyline(short_segment, max_step_miles=0.1)
    assert len(short_densified) == 2

    with pytest.raises(ValueError, match="at least 2 coordinates"):
        densify_polyline((p0,))

    with pytest.raises(ValueError, match="positive finite"):
        densify_polyline((p0, p1), max_step_miles=0.0)


def test_shared_fraction_identical() -> None:
    p0 = Coordinate(32.0, -96.0)
    p1 = Coordinate(33.0, -96.0)
    p2 = Coordinate(34.0, -96.0)
    poly = (p0, p1, p2)

    assert shared_fraction(poly, poly) == 1.0


def test_shared_fraction_disjoint() -> None:
    poly_a = (Coordinate(32.0, -96.0), Coordinate(33.0, -96.0))
    poly_b = (Coordinate(40.0, -105.0), Coordinate(41.0, -105.0))

    assert shared_fraction(poly_a, poly_b) == 0.0


def test_shared_fraction_parallel_offset_1_mile() -> None:
    # Build 10-mile north polyline
    p0 = Coordinate(32.0, -96.0)
    points_a: list[Coordinate] = [p0]
    points_b: list[Coordinate] = []

    for m in range(1, 11):
        pt = offset_point(p0, 0.0, float(m))
        points_a.append(pt)

    # Polyline B is parallel, offset east by exactly 1.0 mile
    for pt in points_a:
        points_b.append(offset_point(pt, 90.0, 1.0))

    poly_a = tuple(points_a)
    poly_b = tuple(points_b)

    # Tolerance is 0.3 miles, so 1.0 mile offset must give 0.0 overlap
    assert shared_fraction(poly_a, poly_b) == 0.0


def test_shared_fraction_half_overlapping() -> None:
    # 20-mile total route: first 10 miles identical, second 10 miles diverging at 90 degrees
    p0 = Coordinate(32.0, -96.0)
    common_pts: list[Coordinate] = [offset_point(p0, 0.0, float(m)) for m in range(11)]

    # Polyline A continues north for 10 more miles
    cand_pts = list(common_pts)
    for m in range(1, 11):
        cand_pts.append(offset_point(common_pts[-1], 0.0, float(m)))

    # Polyline B turns due east for 10 miles
    other_pts = list(common_pts)
    for m in range(1, 11):
        other_pts.append(offset_point(common_pts[-1], 90.0, float(m)))

    frac = shared_fraction(tuple(cand_pts), tuple(other_pts))
    # Approximately half overlapping
    assert 0.45 <= frac <= 0.60


def test_select_routes_three_distinct_kept() -> None:
    origin = Coordinate(32.0, -96.0)
    dest = offset_point(origin, 0.0, 100.0)

    # Three paths between origin and dest: direct, west arc, east arc
    mid_direct = offset_point(origin, 0.0, 50.0)
    mid_west = offset_point(mid_direct, 270.0, 30.0)
    mid_east = offset_point(mid_direct, 90.0, 30.0)

    r1 = _make_route("r1", (origin, mid_direct, dest), 100.0, 5000.0)
    r2 = _make_route("r2", (origin, mid_west, dest), 115.0, 5500.0)
    r3 = _make_route("r3", (origin, mid_east, dest), 118.0, 5800.0)

    selected = select_routes([r1, r2, r3], max_routes=3)
    assert len(selected) == 3
    assert [r.provider_id for r in selected] == ["r1", "r2", "r3"]


def test_select_routes_duplicate_dropped() -> None:
    origin = Coordinate(32.0, -96.0)
    dest = offset_point(origin, 0.0, 100.0)
    mid_west = offset_point(offset_point(origin, 0.0, 50.0), 270.0, 30.0)

    r1 = _make_route("r1", (origin, dest), 100.0, 5000.0)
    r1_dup = _make_route("r1_dup", (origin, dest), 100.0, 5010.0)
    r2 = _make_route("r2", (origin, mid_west, dest), 115.0, 5500.0)

    selected = select_routes([r1, r1_dup, r2], max_routes=3)
    assert len(selected) == 2
    assert "r1" in [r.provider_id for r in selected]
    assert "r2" in [r.provider_id for r in selected]
    assert "r1_dup" not in [r.provider_id for r in selected]


def test_select_routes_detour_over_1_6x_dropped() -> None:
    origin = Coordinate(32.0, -96.0)
    dest = offset_point(origin, 0.0, 100.0)
    mid_west = offset_point(offset_point(origin, 0.0, 50.0), 270.0, 20.0)
    mid_far = offset_point(offset_point(origin, 0.0, 50.0), 270.0, 80.0)

    r1 = _make_route("r1", (origin, dest), 100.0, 4000.0)
    r2 = _make_route("r2", (origin, mid_west, dest), 110.0, 5000.0)  # 1.25x (kept)
    r3 = _make_route("r3", (origin, mid_far, dest), 180.0, 6800.0)  # 1.7x > 1.6x (dropped)

    selected = select_routes([r1, r2, r3], max_routes=3)
    assert len(selected) == 2
    assert [r.provider_id for r in selected] == ["r1", "r2"]


def test_select_routes_overlap_threshold_exact_and_above() -> None:
    origin = Coordinate(32.0, -96.0)
    # Total distance 100 miles
    pts_base = [offset_point(origin, 0.0, float(m)) for m in range(101)]
    r_base = _make_route("r_base", tuple(pts_base), 100.0, 5000.0)

    # Exactly 85% overlap: first 85 miles identical, remaining 15 miles offset east by 5 miles
    pts_85 = list(pts_base[:86])
    for m in range(86, 101):
        pts_85.append(offset_point(pts_base[m], 90.0, 5.0))
    r_85 = _make_route("r_85", tuple(pts_85), 100.0, 5200.0)

    # 90% overlap: first 90 miles identical, remaining 10 miles offset east by 5 miles (> 0.85)
    pts_90 = list(pts_base[:91])
    for m in range(91, 101):
        pts_90.append(offset_point(pts_base[m], 90.0, 5.0))
    r_90 = _make_route("r_90", tuple(pts_90), 100.0, 5100.0)

    # r_85 should qualify because overlap <= 0.85; r_90 should be dropped
    selected = select_routes([r_base, r_85, r_90], max_routes=3)
    assert "r_base" in [r.provider_id for r in selected]
    assert "r_85" in [r.provider_id for r in selected]
    assert "r_90" not in [r.provider_id for r in selected]


def test_select_routes_picks_lowest_overlap_candidate_not_first() -> None:
    origin = Coordinate(32.0, -96.0)
    pts_base = [offset_point(origin, 0.0, float(m)) for m in range(101)]
    r_base = _make_route("r_base", tuple(pts_base), 100.0, 5000.0)

    # Candidate A: duration 5100s, overlap 50%
    pts_a = list(pts_base[:51])
    for m in range(51, 101):
        pts_a.append(offset_point(pts_base[m], 90.0, 5.0))
    r_a = _make_route("r_a", tuple(pts_a), 100.0, 5100.0)

    # Candidate B: duration 5300s, overlap 10%
    pts_b = list(pts_base[:11])
    for m in range(11, 101):
        pts_b.append(offset_point(pts_base[m], 270.0, 10.0))
    r_b = _make_route("r_b", tuple(pts_b), 100.0, 5300.0)

    # Asking for max_routes=2: r_base is kept, then between r_a (50%) and r_b (10%),
    # r_b MUST be picked because it has the lowest overlap!
    selected = select_routes([r_base, r_a, r_b], max_routes=2)
    assert len(selected) == 2
    assert [r.provider_id for r in selected] == ["r_base", "r_b"]


def test_shared_fraction_invalid_polyline_raises() -> None:
    p0 = Coordinate(32.0, -96.0)
    with pytest.raises(ValueError, match="at least 2 coordinates"):
        shared_fraction((p0,), (p0, p0))
    with pytest.raises(ValueError, match="at least 2 coordinates"):
        shared_fraction((p0, p0), (p0,))


def test_shared_fraction_zero_length_polyline() -> None:
    p0 = Coordinate(32.0, -96.0)
    p1 = Coordinate(40.0, -100.0)
    # Zero-distance polyline of duplicate points
    assert shared_fraction((p0, p0), (p0, p0)) == 1.0
    assert shared_fraction((p0, p0), (p1, p1)) == 0.0


def test_select_routes_empty_or_zero_max_routes() -> None:
    assert select_routes([]) == []
    origin = Coordinate(32.0, -96.0)
    r = _make_route("r1", (origin, origin), 10.0, 100.0)
    assert select_routes([r], max_routes=0) == []
    assert select_routes([r], max_routes=-1) == []


def test_offset_point_antimeridian_wrap() -> None:
    # Near 180 degrees longitude
    origin = Coordinate(0.0, 179.9)
    dest = offset_point(origin, bearing_degrees=90.0, miles=20.0)
    assert -180.0 <= dest.lon <= 180.0
    assert dest.lon < 0.0  # Wrapped across +180/-180 meridian
