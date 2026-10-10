import pytest

from core.domain.geometry import (
    cumulative_miles,
    haversine_miles,
    point_at_mile,
    simplify,
)
from core.domain.types import Coordinate


def test_coordinate_valid_values_succeed() -> None:
    c1 = Coordinate(lat=0.0, lon=0.0)
    assert c1.lat == 0.0 and c1.lon == 0.0

    c2 = Coordinate(lat=90.0, lon=180.0)
    assert c2.lat == 90.0 and c2.lon == 180.0

    c3 = Coordinate(lat=-90.0, lon=-180.0)
    assert c3.lat == -90.0 and c3.lon == -180.0

    c4 = Coordinate(lat=37.7749, lon=-122.4194)
    assert c4.lat == 37.7749 and c4.lon == -122.4194


@pytest.mark.parametrize("invalid_lat", [90.01, -90.01, 100.0, -100.0, float("nan"), float("inf")])
def test_coordinate_invalid_latitude_raises_value_error(invalid_lat: float) -> None:
    with pytest.raises(ValueError):
        Coordinate(lat=invalid_lat, lon=0.0)


@pytest.mark.parametrize(
    "invalid_lon", [180.01, -180.01, 200.0, -200.0, float("nan"), float("inf")]
)
def test_coordinate_invalid_longitude_raises_value_error(invalid_lon: float) -> None:
    with pytest.raises(ValueError):
        Coordinate(lat=0.0, lon=invalid_lon)


def test_haversine_miles_known_city_pairs_within_half_percent() -> None:
    # New York City to Los Angeles (~2,451 miles great circle)
    nyc = Coordinate(lat=40.7128, lon=-74.0060)
    la = Coordinate(lat=34.0522, lon=-118.2437)
    dist_nyc_la = haversine_miles(nyc, la)
    expected_nyc_la = 2451.0
    rel_error_nyc_la = abs(dist_nyc_la - expected_nyc_la) / expected_nyc_la
    assert rel_error_nyc_la < 0.005, f"NYC-LA distance {dist_nyc_la} error {rel_error_nyc_la}"

    # Chicago to Houston (~940 miles great circle)
    chicago = Coordinate(lat=41.8781, lon=-87.6298)
    houston = Coordinate(lat=29.7604, lon=-95.3698)
    dist_chi_hou = haversine_miles(chicago, houston)
    expected_chi_hou = 940.0
    rel_error_chi_hou = abs(dist_chi_hou - expected_chi_hou) / expected_chi_hou
    assert rel_error_chi_hou < 0.005, f"Chicago-Houston distance {dist_chi_hou} error"


def test_cumulative_miles_scaling_matches_provider_total_exactly() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=41.0, lon=-80.0),
        Coordinate(lat=42.0, lon=-80.0),
    ]
    target_miles = 150.0
    scaled = cumulative_miles(polyline, target_miles)
    assert len(scaled) == len(polyline)
    assert scaled[0] == 0.0
    assert scaled[-1] == target_miles
    assert scaled[1] == pytest.approx(75.0, abs=1e-6)
    # Monotonic non-decreasing
    for i in range(1, len(scaled)):
        assert scaled[i] >= scaled[i - 1]


def test_cumulative_miles_fewer_than_two_points_raises_value_error() -> None:
    with pytest.raises(ValueError):
        cumulative_miles([Coordinate(lat=40.0, lon=-80.0)], 100.0)


@pytest.mark.parametrize("invalid_total", [0.0, -10.0, float("nan"), float("inf")])
def test_cumulative_miles_invalid_total_miles_raises_value_error(invalid_total: float) -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    with pytest.raises(ValueError):
        cumulative_miles(polyline, invalid_total)


def test_cumulative_miles_zero_geometric_length_raises_value_error() -> None:
    duplicate_polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=40.0, lon=-80.0)]
    with pytest.raises(ValueError):
        cumulative_miles(duplicate_polyline, 50.0)


def test_point_at_mile_at_vertices_returns_exact_coordinates() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=41.0, lon=-80.0),
        Coordinate(lat=42.0, lon=-80.0),
    ]
    cum = [0.0, 50.0, 100.0]

    p0 = point_at_mile(polyline, cum, 0.0)
    assert p0.lat == 40.0 and p0.lon == -80.0

    p1 = point_at_mile(polyline, cum, 50.0)
    assert p1.lat == 41.0 and p1.lon == -80.0

    p2 = point_at_mile(polyline, cum, 100.0)
    assert p2.lat == 42.0 and p2.lon == -80.0


def test_point_at_mile_mid_segment_returns_interpolated_coordinate() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=42.0, lon=-80.0),
    ]
    cum = [0.0, 100.0]

    mid = point_at_mile(polyline, cum, 25.0)
    assert mid.lat == pytest.approx(40.5, abs=1e-6)
    assert mid.lon == pytest.approx(-80.0, abs=1e-6)


def test_point_at_mile_below_zero_clamps_to_first_point() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    cum = [0.0, 50.0]
    p = point_at_mile(polyline, cum, -15.0)
    assert p == polyline[0]


def test_point_at_mile_above_total_clamps_to_last_point() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    cum = [0.0, 50.0]
    p = point_at_mile(polyline, cum, 999.0)
    assert p == polyline[-1]


def test_point_at_mile_zero_length_segment_handles_gracefully() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=41.0, lon=-80.0),
        Coordinate(lat=41.0, lon=-80.0),
        Coordinate(lat=42.0, lon=-80.0),
    ]
    cum = [0.0, 25.0, 25.0, 50.0]
    # Query within duplicate range
    p = point_at_mile(polyline, cum, 25.0)
    assert p.lat == 41.0 and p.lon == -80.0


def test_point_at_mile_fewer_than_two_points_raises_value_error() -> None:
    with pytest.raises(ValueError):
        point_at_mile([Coordinate(lat=40.0, lon=-80.0)], [0.0], 10.0)


def test_point_at_mile_mismatched_lengths_raises_value_error() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    with pytest.raises(ValueError):
        point_at_mile(polyline, [0.0, 50.0, 100.0], 10.0)


@pytest.mark.parametrize("invalid_m", [float("nan"), float("inf"), float("-inf")])
def test_point_at_mile_non_finite_m_raises_value_error(invalid_m: float) -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    with pytest.raises(ValueError, match="m must be a finite number"):
        point_at_mile(polyline, [0.0, 50.0], invalid_m)


def test_simplify_collinear_points_collapses_to_endpoints() -> None:
    # 5 collinear points along longitude -80
    polyline = [Coordinate(lat=40.0 + i * 0.1, lon=-80.0) for i in range(5)]
    simplified = simplify(polyline, tolerance_m=50.0)
    assert len(simplified) == 2
    assert simplified[0] == polyline[0]
    assert simplified[1] == polyline[-1]


def test_simplify_sharp_corner_survives() -> None:
    # Right-angled turn: corner at (40.0, -81.0) is ~50 miles away from direct chord
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=40.0, lon=-81.0),
        Coordinate(lat=41.0, lon=-81.0),
    ]
    simplified = simplify(polyline, tolerance_m=500.0)
    assert len(simplified) == 3
    assert simplified[0] == polyline[0]
    assert simplified[1] == polyline[1]
    assert simplified[2] == polyline[2]


def test_simplify_endpoints_always_kept() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=40.05, lon=-80.01),
        Coordinate(lat=40.1, lon=-80.0),
    ]
    simplified = simplify(polyline, tolerance_m=10_000.0)
    assert len(simplified) == 2
    assert simplified[0] == polyline[0]
    assert simplified[-1] == polyline[-1]


def test_simplify_small_or_zero_tolerance_returns_list_of_points() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=40.5, lon=-80.1),
        Coordinate(lat=41.0, lon=-80.0),
    ]
    assert simplify(polyline[:2], 10.0) == polyline[:2]
    assert simplify(polyline, 0.0) == polyline


def test_simplify_closed_loop_handles_zero_chord_length() -> None:
    # Closed loop where start and end are identical
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=40.5, lon=-80.5),
        Coordinate(lat=40.0, lon=-80.0),
    ]
    simplified = simplify(polyline, tolerance_m=10.0)
    assert len(simplified) == 3
    assert simplified[0] == polyline[0]
    assert simplified[1] == polyline[1]
    assert simplified[2] == polyline[2]


@pytest.mark.parametrize("invalid_tol", [-1.0, float("nan"), float("inf")])
def test_simplify_invalid_tolerance_raises_value_error(invalid_tol: float) -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=40.5, lon=-80.0),
        Coordinate(lat=41.0, lon=-80.0),
    ]
    with pytest.raises(ValueError):
        simplify(polyline, invalid_tol)


def test_simplify_twenty_thousand_points_runs_without_recursion_error() -> None:
    n = 20_000
    polyline = [
        Coordinate(
            lat=40.0 + (i / n) * 1.0 + (0.000001 if i % 2 == 0 else -0.000001),
            lon=-80.0 + (i / n) * 1.0,
        )
        for i in range(n)
    ]
    simplified = simplify(polyline, tolerance_m=50.0)
    assert len(simplified) >= 2
    assert simplified[0] == polyline[0]
    assert simplified[-1] == polyline[-1]
