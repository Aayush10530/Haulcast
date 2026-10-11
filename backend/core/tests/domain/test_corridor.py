"""Tests for pure domain corridor grid generation."""

import pytest

from core.domain import rules_config
from core.domain.corridor import generate_corridor_cells
from core.domain.grid import cell_center
from core.domain.types import Coordinate


def test_corridor_straight_route_gives_three_lanes_per_station() -> None:
    # Straight North route from (35.0, -100.0) to (37.0, -100.0), roughly 138 miles
    route = (Coordinate(lat=35.0, lon=-100.0), Coordinate(lat=37.0, lon=-100.0))
    total_miles = 138.0

    cells = generate_corridor_cells([route], [total_miles])
    assert len(cells) > 0

    # At longitude -100.0 bearing is 0 deg (North), so lateral offsets are East and West.
    # Group cells by latitude index to check that each station spans up to 3 longitude lanes.
    by_lat: dict[int, set[int]] = {}
    for c in cells:
        by_lat.setdefault(c.lat_index, set()).add(c.lon_index)

    # Every station with full lateral span produces 3 lanes (center, left, right)
    lane_counts = [len(lons) for lons in by_lat.values()]
    assert any(count == 3 for count in lane_counts)
    for count in lane_counts:
        assert count in (1, 2, 3)


def test_corridor_overlapping_routes_deduplicate_preserving_order() -> None:
    route1 = (Coordinate(lat=35.0, lon=-100.0), Coordinate(lat=36.0, lon=-100.0))
    route2 = (Coordinate(lat=35.0, lon=-100.0), Coordinate(lat=36.0, lon=-100.0))

    single = generate_corridor_cells([route1], [69.0])
    double = generate_corridor_cells([route1, route2], [69.0, 69.0])

    assert single == double
    assert len(double) == len(set(double))


def test_corridor_deterministic_order() -> None:
    route = (
        Coordinate(lat=32.7767, lon=-96.7970),
        Coordinate(lat=35.1990, lon=-101.8453),
        Coordinate(lat=39.7392, lon=-104.9903),
    )
    total_miles = 800.0

    cells1 = generate_corridor_cells([route], [total_miles])
    cells2 = generate_corridor_cells([route], [total_miles])

    assert cells1 == cells2
    assert len(cells1) == len(set(cells1))


def test_corridor_five_mile_route_gives_at_least_one_cell() -> None:
    # Very short 5-mile route
    route = (Coordinate(lat=35.0, lon=-100.0), Coordinate(lat=35.072, lon=-100.0))
    cells = generate_corridor_cells([route], [5.0])

    assert len(cells) >= 1
    # Check all cells have valid centers
    for cell in cells:
        center = cell_center(cell)
        assert 34.0 < center.lat < 36.0
        assert -101.0 < center.lon < -99.0


def test_corridor_cap_enforced_by_spacing_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    # Route spanning 800 miles
    route = (Coordinate(lat=30.0, lon=-95.0), Coordinate(lat=40.0, lon=-105.0))
    miles = 900.0

    # With standard cap (250)
    normal_cells = generate_corridor_cells([route], [miles])
    assert len(normal_cells) <= 250

    # Artificially constrain cap to 30 to force spacing growth retries
    monkeypatch.setattr(rules_config, "CORRIDOR_MAX_CELLS", 30)
    reduced_cells = generate_corridor_cells([route], [miles])
    assert len(reduced_cells) <= 30
    assert len(reduced_cells) < len(normal_cells)


def test_corridor_exceeding_cap_after_ten_retries_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = (Coordinate(lat=30.0, lon=-95.0), Coordinate(lat=40.0, lon=-105.0))
    miles = 900.0

    # Impossible cap of 0 cells
    monkeypatch.setattr(rules_config, "CORRIDOR_MAX_CELLS", 0)
    with pytest.raises(ValueError, match="exceeds maximum"):
        generate_corridor_cells([route], [miles])


def test_corridor_validation_errors() -> None:
    route = (Coordinate(lat=35.0, lon=-100.0), Coordinate(lat=36.0, lon=-100.0))

    # Mismatched lengths
    with pytest.raises(ValueError, match="length mismatch"):
        generate_corridor_cells([route], [100.0, 200.0])

    # Negative distance
    with pytest.raises(ValueError, match="non-negative finite"):
        generate_corridor_cells([route], [-10.0])

    # Empty routes
    assert generate_corridor_cells([], []) == []

    # Empty polyline
    assert generate_corridor_cells([()], [0.0]) == []

    # Single-point polyline with zero miles
    single = (Coordinate(lat=35.0, lon=-100.0),)
    cells_single = generate_corridor_cells([single], [0.0])
    assert len(cells_single) >= 1

    # Route with identical points
    identical = (Coordinate(lat=35.0, lon=-100.0), Coordinate(lat=35.0, lon=-100.0))
    cells_ident = generate_corridor_cells([identical], [0.0])
    assert len(cells_ident) >= 1


def test_local_bearing_edge_cases() -> None:
    from core.domain.corridor import _local_bearing
    from core.domain.route_diversity import bearing_degrees

    # len < 2
    assert _local_bearing([Coordinate(0.0, 0.0)], [0.0], 0.0) == 0.0

    # idx == 0 (cumulative starts at positive value and m is 0.0)
    poly = [Coordinate(0.0, 0.0), Coordinate(1.0, 0.0)]
    assert _local_bearing(poly, [10.0, 20.0], 0.0) == bearing_degrees(poly[0], poly[1])

    # p1 == p2 with earlier differing segment
    poly2 = [Coordinate(0.0, 0.0), Coordinate(1.0, 0.0), Coordinate(1.0, 0.0)]
    assert _local_bearing(poly2, [0.0, 10.0, 10.0], 10.0) == bearing_degrees(poly2[0], poly2[1])

    # all identical points
    poly3 = [Coordinate(0.0, 0.0), Coordinate(0.0, 0.0)]
    assert _local_bearing(poly3, [0.0, 0.0], 0.0) == 0.0
