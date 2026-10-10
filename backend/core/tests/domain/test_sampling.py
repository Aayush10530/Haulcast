import pytest

from core.domain.sampling import (
    build_checkpoints,
    checkpoint_miles,
    resolve_interval,
)
from core.domain.types import Coordinate, IntervalMode


@pytest.mark.parametrize(
    ("dist", "expected"),
    [
        (0.0, 10),
        (100.0, 10),
        (250.0, 10),
        (250.1, 25),
        (500.0, 25),
        (800.0, 25),
        (800.1, 50),
        (1500.0, 50),
    ],
)
def test_resolve_interval_auto_mode_matches_breakpoints(dist: float, expected: int) -> None:
    assert resolve_interval(IntervalMode.AUTO, None, dist) == expected


@pytest.mark.parametrize("manual_val", [10, 25, 50])
def test_resolve_interval_manual_mode_allowed_intervals(manual_val: int) -> None:
    assert resolve_interval(IntervalMode.MANUAL, manual_val, 100.0) == manual_val


def test_resolve_interval_manual_mode_disallowed_interval_raises_value_error() -> None:
    with pytest.raises(ValueError):
        resolve_interval(IntervalMode.MANUAL, 15, 100.0)


@pytest.mark.parametrize("invalid_dist", [-1.0, float("nan"), float("inf")])
def test_resolve_interval_invalid_distance_raises_value_error(invalid_dist: float) -> None:
    with pytest.raises(ValueError):
        resolve_interval(IntervalMode.AUTO, None, invalid_dist)


def test_resolve_interval_invalid_mode_type_raises_value_error() -> None:
    with pytest.raises(ValueError):
        resolve_interval("auto", None, 100.0)  # type: ignore[arg-type]


def test_checkpoint_miles_total_100_interval_25() -> None:
    miles = checkpoint_miles(100.0, 25)
    assert miles == [0.0, 25.0, 50.0, 75.0, 100.0]


def test_checkpoint_miles_total_60_interval_25() -> None:
    miles = checkpoint_miles(60.0, 25)
    assert miles == [0.0, 25.0, 50.0, 60.0]


def test_checkpoint_miles_total_5_interval_10() -> None:
    miles = checkpoint_miles(5.0, 10)
    assert miles == [0.0, 5.0]


def test_checkpoint_miles_total_50_interval_25_no_duplicate() -> None:
    miles = checkpoint_miles(50.0, 25)
    assert miles == [0.0, 25.0, 50.0]


@pytest.mark.parametrize("invalid_total", [0.0, -10.0, float("nan"), float("inf")])
def test_checkpoint_miles_invalid_total_raises_value_error(invalid_total: float) -> None:
    with pytest.raises(ValueError):
        checkpoint_miles(invalid_total, 25)


@pytest.mark.parametrize("invalid_interval", [0, -5])
def test_checkpoint_miles_invalid_interval_raises_value_error(invalid_interval: int) -> None:
    with pytest.raises(ValueError):
        checkpoint_miles(100.0, invalid_interval)


def test_build_checkpoints_coverage_intervals_100_by_25() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=42.0, lon=-80.0)]
    cum = [0.0, 100.0]
    checkpoints = build_checkpoints(polyline, cum, interval=25)

    expected_coverages = [
        (0.0, 12.5),
        (12.5, 37.5),
        (37.5, 62.5),
        (62.5, 87.5),
        (87.5, 100.0),
    ]
    assert len(checkpoints) == len(expected_coverages)
    for cp, (c_from, c_to) in zip(checkpoints, expected_coverages, strict=True):
        assert cp.covers_from_mile == pytest.approx(c_from)
        assert cp.covers_to_mile == pytest.approx(c_to)


def test_build_checkpoints_coverage_intervals_60_by_25() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=42.0, lon=-80.0)]
    cum = [0.0, 60.0]
    checkpoints = build_checkpoints(polyline, cum, interval=25)

    expected_coverages = [
        (0.0, 12.5),
        (12.5, 37.5),
        (37.5, 55.0),
        (55.0, 60.0),
    ]
    assert len(checkpoints) == len(expected_coverages)
    for cp, (c_from, c_to) in zip(checkpoints, expected_coverages, strict=True):
        assert cp.covers_from_mile == pytest.approx(c_from)
        assert cp.covers_to_mile == pytest.approx(c_to)


def test_build_checkpoints_endpoints_match_polyline_start_and_end() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=41.0, lon=-80.5),
        Coordinate(lat=42.0, lon=-81.0),
    ]
    cum = [0.0, 50.0, 100.0]
    checkpoints = build_checkpoints(polyline, cum, interval=25)

    assert checkpoints[0].coordinate == polyline[0]
    assert checkpoints[-1].coordinate == polyline[-1]


def test_build_checkpoints_handles_duplicate_consecutive_points() -> None:
    polyline = [
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=40.0, lon=-80.0),
        Coordinate(lat=42.0, lon=-80.0),
    ]
    cum = [0.0, 0.0, 100.0]
    checkpoints = build_checkpoints(polyline, cum, interval=25)
    assert len(checkpoints) == 5
    assert checkpoints[0].coordinate == polyline[0]
    assert checkpoints[-1].coordinate == polyline[-1]


def test_build_checkpoints_non_monotonic_cumulative_raises_value_error() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    non_monotonic_cum = [50.0, 40.0]
    with pytest.raises(ValueError):
        build_checkpoints(polyline, non_monotonic_cum, interval=25)


def test_build_checkpoints_mismatched_lengths_raises_value_error() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=41.0, lon=-80.0)]
    with pytest.raises(ValueError):
        build_checkpoints(polyline, [0.0, 25.0, 50.0], interval=25)


def test_build_checkpoints_fewer_than_two_points_raises_value_error() -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0)]
    with pytest.raises(ValueError):
        build_checkpoints(polyline, [0.0], interval=25)


@pytest.mark.parametrize("total", [5.0, 25.0, 60.0, 100.0, 137.5, 800.0, 1234.5])
@pytest.mark.parametrize("interval", [10, 25, 50])
def test_build_checkpoints_coverage_sums_to_total_over_fixed_grid(
    total: float,
    interval: int,
) -> None:
    polyline = [Coordinate(lat=40.0, lon=-80.0), Coordinate(lat=42.0, lon=-80.0)]
    cum = [0.0, total]
    checkpoints = build_checkpoints(polyline, cum, interval=interval)

    # First starts at 0, last ends at total
    assert checkpoints[0].covers_from_mile == 0.0
    assert checkpoints[-1].covers_to_mile == total

    # Contiguity: each interval connects with no gaps or overlaps
    for i in range(len(checkpoints) - 1):
        assert checkpoints[i].covers_to_mile == pytest.approx(
            checkpoints[i + 1].covers_from_mile,
            abs=1e-9,
        )

    # Sum of coverage lengths matches total exactly
    total_coverage = sum(c.covers_to_mile - c.covers_from_mile for c in checkpoints)
    assert total_coverage == pytest.approx(total, abs=1e-9)
