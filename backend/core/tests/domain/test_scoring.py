import datetime

import pytest

from core.domain.geometry import cumulative_miles
from core.domain.sampling import build_checkpoints
from core.domain.scoring import assess_checkpoint, summarize_route
from core.domain.types import (
    AssessedCheckpoint,
    Checkpoint,
    ConditionLevels,
    Coordinate,
    HourlySeries,
    MilesByLevel,
    RiskAssessment,
    RiskDriver,
    RiskLevel,
    RouteSummary,
    WeatherSample,
    WeatherSeries,
)

EPOCH_14_00 = 1_792_072_800
BASE_TIME = datetime.datetime(2026, 10, 15, 14, 0, 0, tzinfo=datetime.UTC)


def _make_dummy_checkpoint(
    index: int = 0,
    mile: float = 0.0,
    from_m: float = 0.0,
    to_m: float = 25.0,
) -> Checkpoint:
    return Checkpoint(
        index=index,
        mile=mile,
        coordinate=Coordinate(lat=40.0, lon=-80.0),
        covers_from_mile=from_m,
        covers_to_mile=to_m,
    )


def _make_dummy_assessed(
    checkpoint: Checkpoint,
    level: RiskLevel | None,
) -> AssessedCheckpoint:
    if level is None:
        return AssessedCheckpoint(
            checkpoint=checkpoint,
            eta_utc=BASE_TIME,
            tz_name="UTC",
            sample=None,
            assessment=None,
            reason=None,
        )

    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    assessment = RiskAssessment(
        level=level,
        table_level=level,
        driver=RiskDriver.WIND,
        load_rule_applied=False,
        per_condition_levels=ConditionLevels(wind=level, rain=RiskLevel.LOW, snow=RiskLevel.LOW),
    )
    return AssessedCheckpoint(
        checkpoint=checkpoint,
        eta_utc=BASE_TIME,
        tz_name="UTC",
        sample=sample,
        assessment=assessment,
        reason=f"Level {level.name}",
    )


def test_summarize_route_one_hundred_miles_fixed_intervals_calculates_expected_summary() -> None:
    # 100 mi route at interval 25 has 5 checkpoints:
    # cp 0: mile 0, covers [0, 12.5] (12.5 mi) -> LOW
    # cp 1: mile 25, covers [12.5, 37.5] (25.0 mi) -> MODERATE
    # cp 2: mile 50, covers [37.5, 62.5] (25.0 mi) -> HIGH
    # cp 3: mile 75, covers [62.5, 87.5] (25.0 mi) -> SEVERE
    # cp 4: mile 100, covers [87.5, 100.0] (12.5 mi) -> LOW
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 12.5),
        _make_dummy_checkpoint(1, 25.0, 12.5, 37.5),
        _make_dummy_checkpoint(2, 50.0, 37.5, 62.5),
        _make_dummy_checkpoint(3, 75.0, 62.5, 87.5),
        _make_dummy_checkpoint(4, 100.0, 87.5, 100.0),
    ]
    levels = [
        RiskLevel.LOW,
        RiskLevel.MODERATE,
        RiskLevel.HIGH,
        RiskLevel.SEVERE,
        RiskLevel.LOW,
    ]
    assessed = [_make_dummy_assessed(cp, lvl) for cp, lvl in zip(cps, levels, strict=True)]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=7200.0)

    assert summary.distance_miles == 100.0
    assert summary.duration_seconds == 7200.0
    assert summary.miles_by_level.low == 25.0  # 12.5 + 12.5
    assert summary.miles_by_level.moderate == 25.0
    assert summary.miles_by_level.high == 25.0
    assert summary.miles_by_level.severe == 25.0
    assert summary.miles_by_level.no_travel == 0.0
    assert summary.unavailable_miles == 0.0
    assert summary.unavailable_checkpoints == 0
    # Avg: (0*25 + 1*25 + 2*25 + 3*25)/100 = 150/100 = 1.5
    assert summary.avg_risk_score == pytest.approx(1.5)
    assert summary.max_level == RiskLevel.SEVERE
    assert not summary.has_no_travel


def test_summarize_route_unavailable_in_middle_tracked_and_excluded_from_avg() -> None:
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 20.0),
        _make_dummy_checkpoint(1, 40.0, 20.0, 60.0),
        _make_dummy_checkpoint(2, 80.0, 60.0, 100.0),
    ]
    # cp 1 is unavailable
    assessed = [
        _make_dummy_assessed(cps[0], RiskLevel.LOW),
        _make_dummy_assessed(cps[1], None),
        _make_dummy_assessed(cps[2], RiskLevel.HIGH),
    ]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=6000.0)

    assert summary.unavailable_miles == 40.0
    assert summary.unavailable_checkpoints == 1
    assert summary.miles_by_level.low == 20.0
    assert summary.miles_by_level.high == 40.0
    # Avg over 60 assessed miles: (0*20 + 2*40) / 60 = 80 / 60 = 1.333333
    assert summary.avg_risk_score == pytest.approx(80.0 / 60.0)
    assert summary.max_level == RiskLevel.HIGH


def test_summarize_route_all_unavailable_returns_none_average_and_max_level() -> None:
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 50.0),
        _make_dummy_checkpoint(1, 50.0, 50.0, 100.0),
    ]
    assessed = [_make_dummy_assessed(cp, None) for cp in cps]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=5000.0)

    assert summary.unavailable_miles == 100.0
    assert summary.unavailable_checkpoints == 2
    assert summary.avg_risk_score is None
    assert summary.max_level is None
    assert not summary.has_no_travel


def test_summarize_route_all_low_returns_zero_average() -> None:
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 50.0),
        _make_dummy_checkpoint(1, 50.0, 50.0, 100.0),
    ]
    assessed = [_make_dummy_assessed(cp, RiskLevel.LOW) for cp in cps]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=5000.0)

    assert summary.avg_risk_score == 0.0
    assert summary.max_level == RiskLevel.LOW
    assert not summary.has_no_travel


def test_summarize_route_unavailable_with_all_assessed_no_travel_returns_exactly_four_average() -> (
    None
):
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 50.0),
        _make_dummy_checkpoint(1, 50.0, 50.0, 100.0),
    ]
    assessed = [
        _make_dummy_assessed(cps[0], None),
        _make_dummy_assessed(cps[1], RiskLevel.NO_TRAVEL),
    ]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=5000.0)

    assert summary.avg_risk_score == 4.0
    assert summary.max_level == RiskLevel.NO_TRAVEL
    assert summary.has_no_travel
    assert summary.unavailable_miles == 50.0
    assert summary.miles_by_level.no_travel == 50.0


def test_summarize_route_all_assessed_low_with_unavailable_returns_zero_average() -> None:
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 40.0),
        _make_dummy_checkpoint(1, 40.0, 40.0, 100.0),
    ]
    assessed = [
        _make_dummy_assessed(cps[0], None),
        _make_dummy_assessed(cps[1], RiskLevel.LOW),
    ]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=5000.0)

    assert summary.avg_risk_score == 0.0
    assert summary.max_level == RiskLevel.LOW
    assert not summary.has_no_travel
    assert summary.unavailable_miles == 40.0
    assert summary.miles_by_level.low == 60.0


def test_summarize_route_assessed_miles_zero_with_levels_returns_none_average() -> None:
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 0.0),
        _make_dummy_checkpoint(1, 0.0, 0.0, 10.0),
    ]
    assessed = [
        _make_dummy_assessed(cps[0], RiskLevel.LOW),
        _make_dummy_assessed(cps[1], None),
    ]

    summary = summarize_route(assessed, distance_miles=10.0, duration_seconds=1000.0)

    assert summary.max_level == RiskLevel.LOW
    assert summary.avg_risk_score is None
    assert summary.unavailable_miles == 10.0


def test_summarize_route_single_no_travel_tiny_coverage_sets_has_no_travel() -> None:
    cps = [
        _make_dummy_checkpoint(0, 0.0, 0.0, 99.99),
        _make_dummy_checkpoint(1, 99.99, 99.99, 100.0),
    ]
    # Second checkpoint has only 0.01 mi coverage but is NO_TRAVEL
    assessed = [
        _make_dummy_assessed(cps[0], RiskLevel.LOW),
        _make_dummy_assessed(cps[1], RiskLevel.NO_TRAVEL),
    ]

    summary = summarize_route(assessed, distance_miles=100.0, duration_seconds=4000.0)

    assert summary.max_level == RiskLevel.NO_TRAVEL
    assert summary.has_no_travel
    assert summary.miles_by_level.no_travel == pytest.approx(0.01)


@pytest.mark.parametrize("interval", [10, 25, 50])
@pytest.mark.parametrize("total_dist", [15.0, 60.0, 137.5, 800.0])
def test_summarize_route_sum_of_miles_matches_distance_within_tolerance(
    interval: int, total_dist: float
) -> None:
    polyline = [
        Coordinate(lat=30.0, lon=-80.0),
        Coordinate(lat=35.0, lon=-80.0),
    ]
    cum = cumulative_miles(polyline, total_dist)
    checkpoints = build_checkpoints(polyline, cum, interval=interval)

    # Alternate levels and one unavailable
    assessed = []
    for i, cp in enumerate(checkpoints):
        lvl = None if i == 1 else RiskLevel(i % 5)
        assessed.append(_make_dummy_assessed(cp, lvl))

    summary = summarize_route(assessed, distance_miles=total_dist, duration_seconds=3600.0)

    summed_miles = (
        summary.miles_by_level.low
        + summary.miles_by_level.moderate
        + summary.miles_by_level.high
        + summary.miles_by_level.severe
        + summary.miles_by_level.no_travel
        + summary.unavailable_miles
    )
    assert abs(summed_miles - total_dist) <= 1e-9


def test_summarize_route_coverage_mismatch_raises_value_error() -> None:
    cps = [_make_dummy_checkpoint(0, 0.0, 0.0, 80.0)]
    assessed = [_make_dummy_assessed(cps[0], RiskLevel.LOW)]

    # Coverage is 80, distance is 100 -> relative diff 0.2 > 1e-6
    with pytest.raises(ValueError, match="differs from route distance"):
        summarize_route(assessed, distance_miles=100.0, duration_seconds=3600.0)


def test_summarize_route_empty_list_raises_value_error() -> None:
    with pytest.raises(ValueError, match="sequence cannot be empty"):
        summarize_route([], distance_miles=100.0, duration_seconds=3600.0)


@pytest.mark.parametrize(
    ("dist", "dur"),
    [
        (0.0, 3600.0),
        (-10.0, 3600.0),
        (float("nan"), 3600.0),
        (float("inf"), 3600.0),
        (100.0, -1.0),
        (100.0, float("nan")),
        (100.0, float("inf")),
    ],
)
def test_summarize_route_invalid_distance_or_duration_raises_value_error(
    dist: float, dur: float
) -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 100.0)
    assessed = [_make_dummy_assessed(cp, RiskLevel.LOW)]
    with pytest.raises(ValueError):
        summarize_route(assessed, distance_miles=dist, duration_seconds=dur)


def test_assessed_checkpoint_mismatched_sample_and_assessment_raises_value_error() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    assessment = RiskAssessment(
        level=RiskLevel.LOW,
        table_level=RiskLevel.LOW,
        driver=RiskDriver.WIND,
        load_rule_applied=False,
        per_condition_levels=ConditionLevels(
            wind=RiskLevel.LOW, rain=RiskLevel.LOW, snow=RiskLevel.LOW
        ),
    )

    # Sample without assessment
    with pytest.raises(ValueError, match="sample and assessment must both be None"):
        AssessedCheckpoint(
            checkpoint=cp,
            eta_utc=BASE_TIME,
            tz_name="UTC",
            sample=sample,
            assessment=None,
            reason="Sample provided",
        )

    # Assessment without sample
    with pytest.raises(ValueError, match="sample and assessment must both be None"):
        AssessedCheckpoint(
            checkpoint=cp,
            eta_utc=BASE_TIME,
            tz_name="UTC",
            sample=None,
            assessment=assessment,
            reason="Assessment provided",
        )


def test_assessed_checkpoint_validation_reason_mismatch_raises_value_error() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    assessment = RiskAssessment(
        level=RiskLevel.LOW,
        table_level=RiskLevel.LOW,
        driver=RiskDriver.WIND,
        load_rule_applied=False,
        per_condition_levels=ConditionLevels(
            wind=RiskLevel.LOW, rain=RiskLevel.LOW, snow=RiskLevel.LOW
        ),
    )

    # Assessment provided but reason is None
    with pytest.raises(ValueError, match="reason must be provided if and only if"):
        AssessedCheckpoint(
            checkpoint=cp,
            eta_utc=BASE_TIME,
            tz_name="UTC",
            sample=sample,
            assessment=assessment,
            reason=None,
        )

    # No assessment but reason is provided
    with pytest.raises(ValueError, match="reason must be provided if and only if"):
        AssessedCheckpoint(
            checkpoint=cp,
            eta_utc=BASE_TIME,
            tz_name="UTC",
            sample=None,
            assessment=None,
            reason="Reason without assessment",
        )


def test_assessed_checkpoint_validation_naive_eta_raises_value_error() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    naive_dt = datetime.datetime(2026, 10, 15, 14, 0, 0)
    with pytest.raises(ValueError, match="eta_utc must be a timezone-aware datetime"):
        AssessedCheckpoint(
            checkpoint=cp,
            eta_utc=naive_dt,
            tz_name="UTC",
            sample=None,
            assessment=None,
            reason=None,
        )


def test_assess_checkpoint_normal_sample_matches_risk_assess_and_describe() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    ws = WeatherSeries(
        tz_name="America/New_York",
        wind_mph=HourlySeries(EPOCH_14_00, (12.4, 12.4)),
        rain_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
        snow_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
    )

    assessed = assess_checkpoint(cp, BASE_TIME, ws, load_weight_lb=50_000.0)

    assert assessed.sample == WeatherSample(wind_mph=12.4, rain_in_hr=0.0, snow_in_hr=0.0)
    assert assessed.assessment is not None
    assert assessed.assessment.level == RiskLevel.LOW
    assert assessed.reason == "Wind 12.4 mph is Low."
    assert assessed.tz_name == "America/New_York"


def test_assess_checkpoint_load_rule_applied_elevates_level_and_flag() -> None:
    # Wind 40.0 mph with load 45,000 lb triggers load rule elevating to Severe
    cp = _make_dummy_checkpoint(1, 25.0, 12.5, 37.5)
    ws = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_14_00, (40.0, 40.0)),
        rain_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
        snow_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
    )

    assessed = assess_checkpoint(cp, BASE_TIME, ws, load_weight_lb=45_000.0)

    assert assessed.assessment is not None
    assert assessed.assessment.level == RiskLevel.SEVERE
    assert assessed.assessment.table_level == RiskLevel.HIGH
    assert assessed.assessment.load_rule_applied
    assert assessed.assessment.driver == RiskDriver.LOAD_RULE
    assert "load 45,000 lb over 40,000 lb makes it Severe." in (assessed.reason or "")


def test_assess_checkpoint_series_none_returns_unavailable() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    assessed = assess_checkpoint(cp, BASE_TIME, series=None, load_weight_lb=30_000.0)

    assert assessed.sample is None
    assert assessed.assessment is None
    assert assessed.reason is None
    assert assessed.tz_name == ""


def test_assess_checkpoint_eta_beyond_series_end_returns_unavailable() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    ws = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_14_00, (10.0, 10.0)),
        rain_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
        snow_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
    )
    # 5 hours past series end
    far_eta = datetime.datetime(2026, 10, 15, 20, 0, 0, tzinfo=datetime.UTC)

    assessed = assess_checkpoint(cp, far_eta, ws, load_weight_lb=30_000.0)

    assert assessed.sample is None
    assert assessed.assessment is None
    assert assessed.reason is None


def test_assess_checkpoint_interpolated_wind_crosses_boundary_before_classification() -> None:
    # 14:00 wind is 20.0 mph (Low), 15:00 wind is 40.0 mph (High)
    # At 14:30: linear interpolation gives 30.0 mph -> classified as Moderate!
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    ws = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_14_00, (20.0, 40.0)),
        rain_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
        snow_in_hr=HourlySeries(EPOCH_14_00, (0.0, 0.0)),
    )
    eta_14_30 = datetime.datetime(2026, 10, 15, 14, 30, 0, tzinfo=datetime.UTC)

    assessed = assess_checkpoint(cp, eta_14_30, ws, load_weight_lb=10_000.0)

    assert assessed.sample is not None
    assert assessed.sample.wind_mph == pytest.approx(30.0)
    assert assessed.assessment is not None
    assert assessed.assessment.level == RiskLevel.MODERATE


def test_miles_by_level_for_level_lookup_returns_correct_value() -> None:
    mbl = MilesByLevel(low=10.0, moderate=20.0, high=30.0, severe=40.0, no_travel=50.0)
    assert mbl.for_level(RiskLevel.LOW) == 10.0
    assert mbl.for_level(RiskLevel.MODERATE) == 20.0
    assert mbl.for_level(RiskLevel.HIGH) == 30.0
    assert mbl.for_level(RiskLevel.SEVERE) == 40.0
    assert mbl.for_level(RiskLevel.NO_TRAVEL) == 50.0


@pytest.mark.parametrize("invalid_val", [-1.0, float("nan"), float("inf")])
def test_miles_by_level_invalid_values_raises_value_error(invalid_val: float) -> None:
    with pytest.raises(ValueError):
        MilesByLevel(low=invalid_val, moderate=0.0, high=0.0, severe=0.0, no_travel=0.0)


@pytest.mark.parametrize("invalid_score", [-0.5, 4.5, float("nan"), float("inf")])
def test_route_summary_invalid_avg_risk_score_raises_value_error(invalid_score: float) -> None:
    mbl = MilesByLevel(0.0, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        RouteSummary(
            distance_miles=100.0,
            duration_seconds=3600.0,
            miles_by_level=mbl,
            unavailable_miles=0.0,
            avg_risk_score=invalid_score,
            max_level=None,
            unavailable_checkpoints=0,
        )


def test_route_summary_negative_unavailable_checkpoints_raises_value_error() -> None:
    mbl = MilesByLevel(0.0, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        RouteSummary(
            distance_miles=100.0,
            duration_seconds=3600.0,
            miles_by_level=mbl,
            unavailable_miles=0.0,
            avg_risk_score=None,
            max_level=None,
            unavailable_checkpoints=-1,
        )


def test_assess_checkpoint_naive_eta_raises_value_error() -> None:
    cp = _make_dummy_checkpoint(0, 0.0, 0.0, 25.0)
    naive_dt = datetime.datetime(2026, 10, 15, 14, 0, 0)
    with pytest.raises(ValueError, match="eta_utc must be a timezone-aware datetime"):
        assess_checkpoint(cp, naive_dt, series=None, load_weight_lb=30_000.0)


@pytest.mark.parametrize(
    ("dist", "dur", "unavail"),
    [
        (-10.0, 3600.0, 0.0),
        (100.0, -10.0, 0.0),
        (100.0, 3600.0, -5.0),
    ],
)
def test_route_summary_invalid_distances_or_durations_raises_value_error(
    dist: float, dur: float, unavail: float
) -> None:
    mbl = MilesByLevel(0.0, 0.0, 0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        RouteSummary(
            distance_miles=dist,
            duration_seconds=dur,
            miles_by_level=mbl,
            unavailable_miles=unavail,
            avg_risk_score=None,
            max_level=None,
            unavailable_checkpoints=0,
        )
