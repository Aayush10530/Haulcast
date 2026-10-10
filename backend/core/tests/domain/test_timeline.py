import datetime
import zoneinfo

import pytest

from core.domain.geometry import cumulative_miles
from core.domain.sampling import build_checkpoints
from core.domain.timeline import (
    constant_speed_timeline,
    elapsed_at,
    eta_at,
    etas_for_checkpoints,
)
from core.domain.types import Coordinate, Timeline


def test_elapsed_at_constant_speed_zero_returns_zero() -> None:
    tl = constant_speed_timeline(total_miles=100.0, total_seconds=7200.0)
    assert elapsed_at(tl, 0.0) == 0.0


def test_elapsed_at_constant_speed_half_returns_half_duration() -> None:
    tl = constant_speed_timeline(total_miles=100.0, total_seconds=7200.0)
    assert elapsed_at(tl, 50.0) == 3600.0


def test_elapsed_at_constant_speed_total_returns_total_duration() -> None:
    tl = constant_speed_timeline(total_miles=100.0, total_seconds=7200.0)
    assert elapsed_at(tl, 100.0) == 7200.0


def test_elapsed_at_piecewise_three_speeds_returns_interpolated_seconds() -> None:
    # Seg 1: 0 to 30 mi at 30 mph -> duration 30/30 * 3600 = 3600 s. Point: (30.0, 3600.0)
    # Seg 2: 30 to 90 mi (60 mi) at 60 mph -> duration 60/60 * 3600 = 3600 s. Point: (90.0, 7200.0)
    # Seg 3: 90 to 100 mi (10 mi) at 40 mph -> duration 10/40 * 3600 = 900 s. Point: (100.0, 8100.0)
    tl = Timeline.from_points(
        [
            (0.0, 0.0),
            (30.0, 3600.0),
            (90.0, 7200.0),
            (100.0, 8100.0),
        ]
    )

    assert elapsed_at(tl, 15.0) == pytest.approx(1800.0)
    assert elapsed_at(tl, 30.0) == 3600.0
    assert elapsed_at(tl, 60.0) == pytest.approx(5400.0)
    assert elapsed_at(tl, 90.0) == 7200.0
    assert elapsed_at(tl, 95.0) == pytest.approx(7650.0)
    assert elapsed_at(tl, 100.0) == 8100.0


def test_elapsed_at_below_zero_clamps_to_zero() -> None:
    tl = constant_speed_timeline(total_miles=50.0, total_seconds=3000.0)
    assert elapsed_at(tl, -10.0) == 0.0


def test_elapsed_at_above_total_clamps_to_total_seconds() -> None:
    tl = constant_speed_timeline(total_miles=50.0, total_seconds=3000.0)
    assert elapsed_at(tl, 75.0) == 3000.0


def test_elapsed_at_duplicate_distance_points_returns_later_elapsed() -> None:
    # Delay/stop at mile 20 from t=1200s to t=1800s
    tl = Timeline.from_points(
        [
            (0.0, 0.0),
            (20.0, 1200.0),
            (20.0, 1800.0),
            (50.0, 3600.0),
        ]
    )
    assert elapsed_at(tl, 20.0) == 1800.0


def test_elapsed_at_exact_interior_vertex_returns_exact_elapsed() -> None:
    tl = Timeline.from_points(
        [
            (0.0, 0.0),
            (25.0, 1500.0),
            (50.0, 3000.0),
        ]
    )
    assert elapsed_at(tl, 25.0) == 1500.0


@pytest.mark.parametrize("invalid_m", [float("nan"), float("inf"), float("-inf")])
def test_elapsed_at_nan_or_inf_mile_raises_value_error(invalid_m: float) -> None:
    tl = constant_speed_timeline(total_miles=50.0, total_seconds=3000.0)
    with pytest.raises(ValueError, match="mile must be a finite number"):
        elapsed_at(tl, invalid_m)


def test_timeline_first_point_not_zero_raises_value_error() -> None:
    with pytest.raises(ValueError, match="First point of timeline must be"):
        Timeline.from_points([(1.0, 0.0), (10.0, 600.0)])
    with pytest.raises(ValueError, match="First point of timeline must be"):
        Timeline.from_points([(0.0, 10.0), (10.0, 600.0)])


def test_timeline_fewer_than_two_points_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Timeline must contain at least 2 points"):
        Timeline.from_points([(0.0, 0.0)])


def test_timeline_decreasing_distance_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Distances must be non-decreasing"):
        Timeline.from_points([(0.0, 0.0), (50.0, 1000.0), (40.0, 1500.0)])


def test_timeline_decreasing_elapsed_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Elapsed seconds must be non-decreasing"):
        Timeline.from_points([(0.0, 0.0), (20.0, 1500.0), (40.0, 1200.0)])


@pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
def test_timeline_nan_or_infinity_raises_value_error(bad_val: float) -> None:
    with pytest.raises(ValueError):
        Timeline.from_points([(0.0, 0.0), (bad_val, 1000.0)])
    with pytest.raises(ValueError):
        Timeline.from_points([(0.0, 0.0), (50.0, bad_val)])


def test_timeline_negative_values_raises_value_error() -> None:
    with pytest.raises(ValueError):
        Timeline(distances_miles=(0.0, -5.0), elapsed_seconds=(0.0, 100.0))
    with pytest.raises(ValueError):
        Timeline(distances_miles=(0.0, 10.0), elapsed_seconds=(0.0, -50.0))


def test_timeline_mismatched_tuple_lengths_raises_value_error() -> None:
    with pytest.raises(ValueError, match="matching lengths"):
        Timeline(distances_miles=(0.0, 10.0), elapsed_seconds=(0.0, 500.0, 1000.0))


def test_timeline_delay_at_start_rejected() -> None:
    with pytest.raises(ValueError, match="Point at distance 0 must have elapsed 0"):
        Timeline.from_points([(0.0, 0.0), (0.0, 300.0), (50.0, 3000.0)])


@pytest.mark.parametrize(
    ("dist", "secs"),
    [
        (0.0, 100.0),
        (-10.0, 100.0),
        (float("nan"), 100.0),
        (float("inf"), 100.0),
        (50.0, -1.0),
        (50.0, float("nan")),
        (50.0, float("inf")),
    ],
)
def test_constant_speed_timeline_invalid_inputs_raises_value_error(
    dist: float, secs: float
) -> None:
    with pytest.raises(ValueError):
        constant_speed_timeline(total_miles=dist, total_seconds=secs)


def test_eta_at_naive_datetime_raises_value_error() -> None:
    tl = constant_speed_timeline(total_miles=100.0, total_seconds=3600.0)
    naive_dt = datetime.datetime(2026, 10, 15, 8, 0, 0)
    with pytest.raises(ValueError, match="departure must be a timezone-aware datetime"):
        eta_at(naive_dt, tl, 50.0)


def test_eta_at_non_utc_aware_datetime_converts_to_utc() -> None:
    tl = constant_speed_timeline(total_miles=100.0, total_seconds=3600.0)
    tz_ny = zoneinfo.ZoneInfo("America/New_York")
    # 2026-10-15 08:00:00 EDT is UTC-4 -> 12:00:00 UTC
    departure_ny = datetime.datetime(2026, 10, 15, 8, 0, 0, tzinfo=tz_ny)

    eta = eta_at(departure_ny, tl, 50.0)
    assert eta.tzinfo == datetime.UTC
    # 50 miles = 1800 seconds (30 minutes) -> 12:30:00 UTC
    expected = datetime.datetime(2026, 10, 15, 12, 30, 0, tzinfo=datetime.UTC)
    assert eta == expected


def test_eta_at_fifty_hour_trip_crossing_midnight_calculates_correct_utc_datetime() -> None:
    # 50-hour trip: 50 * 3600 = 180,000 seconds
    tl = constant_speed_timeline(total_miles=2500.0, total_seconds=180_000.0)
    departure = datetime.datetime(2026, 10, 15, 22, 0, 0, tzinfo=datetime.UTC)

    eta_end = eta_at(departure, tl, 2500.0)
    # Departs Oct 15 22:00 UTC, +50 hours -> Oct 18 00:00 UTC (spans Oct 16 and Oct 17 midnights)
    expected = datetime.datetime(2026, 10, 18, 0, 0, 0, tzinfo=datetime.UTC)
    assert eta_end == expected
    assert (eta_end - departure).total_seconds() == 180_000.0


def test_etas_for_checkpoints_empty_list_returns_empty_list() -> None:
    tl = constant_speed_timeline(total_miles=100.0, total_seconds=3600.0)
    dep = datetime.datetime(2026, 10, 15, 8, 0, 0, tzinfo=datetime.UTC)
    assert etas_for_checkpoints(dep, tl, []) == []


def test_etas_for_checkpoints_piecewise_integration_monotonic_and_endpoints_match() -> None:
    polyline = [
        Coordinate(lat=35.0, lon=-85.0),
        Coordinate(lat=36.0, lon=-85.0),
        Coordinate(lat=37.0, lon=-85.0),
        Coordinate(lat=38.0, lon=-85.0),
    ]
    total_miles = 210.0
    cum = cumulative_miles(polyline, total_miles)
    checkpoints = build_checkpoints(polyline, cum, interval=25)

    # Piecewise timeline with 3 distinct speeds:
    # 0 to 50 mi: 25 mph -> 7200 s
    # 50 to 150 mi (100 mi): 50 mph -> 7200 s (cum 14400 s)
    # 150 to 210 mi (60 mi): 60 mph -> 3600 s (cum 18000 s)
    total_seconds = 18000.0
    tl = Timeline.from_points(
        [
            (0.0, 0.0),
            (50.0, 7200.0),
            (150.0, 14400.0),
            (210.0, total_seconds),
        ]
    )

    departure = datetime.datetime(2026, 10, 15, 6, 0, 0, tzinfo=datetime.UTC)
    etas = etas_for_checkpoints(departure, tl, checkpoints)

    assert len(etas) == len(checkpoints)

    # First checkpoint ETA equals departure
    assert etas[0] == departure

    # Non-decreasing ETAs
    for i in range(1, len(etas)):
        assert etas[i] >= etas[i - 1]

    # Last checkpoint ETA equals departure + total_seconds within 1 microsecond
    expected_end = departure + datetime.timedelta(seconds=total_seconds)
    delta_us = abs((etas[-1] - expected_end).total_seconds()) * 1_000_000
    assert delta_us <= 1.0
