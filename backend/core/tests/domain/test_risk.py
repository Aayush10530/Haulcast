import pytest

from core.domain.risk import assess, classify_rain, classify_snow, classify_wind, describe
from core.domain.types import (
    RiskDriver,
    RiskLevel,
    WeatherSample,
)


def test_risk_level_properties_returns_expected_keys_and_labels() -> None:
    expected = [
        (RiskLevel.LOW, "low", "Low"),
        (RiskLevel.MODERATE, "moderate", "Moderate"),
        (RiskLevel.HIGH, "high", "High"),
        (RiskLevel.SEVERE, "severe", "Severe"),
        (RiskLevel.NO_TRAVEL, "no_travel", "No Travel"),
    ]
    for level, expected_key, expected_label in expected:
        assert level.key == expected_key
        assert level.label == expected_label


@pytest.mark.parametrize(
    ("val", "expected"),
    [
        (0.0, RiskLevel.LOW),
        (24.9, RiskLevel.LOW),
        (25.0, RiskLevel.MODERATE),
        (34.9, RiskLevel.MODERATE),
        (35.0, RiskLevel.HIGH),
        (44.9, RiskLevel.HIGH),
        (45.0, RiskLevel.SEVERE),
        (54.9, RiskLevel.SEVERE),
        (55.0, RiskLevel.NO_TRAVEL),
        (60.0, RiskLevel.NO_TRAVEL),
    ],
)
def test_classify_wind_boundary_pairs_returns_expected_level(
    val: float,
    expected: RiskLevel,
) -> None:
    assert classify_wind(val) == expected


@pytest.mark.parametrize(
    ("val", "expected"),
    [
        (0.0, RiskLevel.LOW),
        (0.09, RiskLevel.LOW),
        (0.10, RiskLevel.MODERATE),
        (0.24, RiskLevel.MODERATE),
        (0.25, RiskLevel.HIGH),
        (0.49, RiskLevel.HIGH),
        (0.50, RiskLevel.SEVERE),
        (1.00, RiskLevel.SEVERE),
        (1.01, RiskLevel.NO_TRAVEL),
        (2.00, RiskLevel.NO_TRAVEL),
    ],
)
def test_classify_rain_boundary_pairs_returns_expected_level(
    val: float,
    expected: RiskLevel,
) -> None:
    assert classify_rain(val) == expected


@pytest.mark.parametrize(
    ("val", "expected"),
    [
        (0.0, RiskLevel.LOW),
        (0.4, RiskLevel.LOW),
        (0.5, RiskLevel.MODERATE),
        (0.9, RiskLevel.MODERATE),
        (1.0, RiskLevel.HIGH),
        (1.9, RiskLevel.HIGH),
        (2.0, RiskLevel.SEVERE),
        (3.00, RiskLevel.SEVERE),
        (3.01, RiskLevel.NO_TRAVEL),
        (4.00, RiskLevel.NO_TRAVEL),
    ],
)
def test_classify_snow_boundary_pairs_returns_expected_level(
    val: float,
    expected: RiskLevel,
) -> None:
    assert classify_snow(val) == expected


def test_classify_wind_monotonic_sweep_non_decreasing() -> None:
    sweep = [
        0.0,
        10.0,
        24.9,
        25.0,
        30.0,
        34.9,
        35.0,
        40.0,
        44.9,
        45.0,
        50.0,
        54.9,
        55.0,
        60.0,
        100.0,
    ]
    levels = [classify_wind(v) for v in sweep]
    for i in range(len(levels) - 1):
        assert levels[i] <= levels[i + 1]


def test_classify_rain_monotonic_sweep_non_decreasing() -> None:
    sweep = [
        0.0,
        0.05,
        0.09,
        0.10,
        0.20,
        0.24,
        0.25,
        0.40,
        0.49,
        0.50,
        0.80,
        1.00,
        1.01,
        1.50,
        2.00,
    ]
    levels = [classify_rain(v) for v in sweep]
    for i in range(len(levels) - 1):
        assert levels[i] <= levels[i + 1]


def test_classify_snow_monotonic_sweep_non_decreasing() -> None:
    sweep = [0.0, 0.2, 0.4, 0.5, 0.8, 0.9, 1.0, 1.5, 1.9, 2.0, 2.5, 3.0, 3.01, 3.5, 5.0]
    levels = [classify_snow(v) for v in sweep]
    for i in range(len(levels) - 1):
        assert levels[i] <= levels[i + 1]


@pytest.mark.parametrize("invalid_val", [-0.1, -10.0, float("nan"), float("inf"), -float("inf")])
def test_classify_wind_invalid_inputs_raises_value_error(invalid_val: float) -> None:
    with pytest.raises(ValueError):
        classify_wind(invalid_val)


@pytest.mark.parametrize("invalid_val", [-0.01, -1.0, float("nan"), float("inf"), -float("inf")])
def test_classify_rain_invalid_inputs_raises_value_error(invalid_val: float) -> None:
    with pytest.raises(ValueError):
        classify_rain(invalid_val)


@pytest.mark.parametrize("invalid_val", [-0.1, -1.0, float("nan"), float("inf"), -float("inf")])
def test_classify_snow_invalid_inputs_raises_value_error(invalid_val: float) -> None:
    with pytest.raises(ValueError):
        classify_snow(invalid_val)


@pytest.mark.parametrize("invalid_load", [-1.0, -100.0, float("nan"), float("inf"), -float("inf")])
def test_assess_invalid_load_weight_raises_value_error(invalid_load: float) -> None:
    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    with pytest.raises(ValueError):
        assess(sample, invalid_load)


def test_assess_zero_load_allowed_returns_valid_assessment() -> None:
    sample = WeatherSample(wind_mph=0.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(sample, 0.0)
    assert res.level == RiskLevel.LOW
    assert res.table_level == RiskLevel.LOW
    assert res.driver == RiskDriver.WIND
    assert res.load_rule_applied is False


@pytest.mark.parametrize(
    ("wind", "rain", "snow", "load", "expected_level", "expected_driver"),
    [
        (20.0, 0.0, 0.0, 50_000.0, RiskLevel.LOW, RiskDriver.WIND),
        (50.0, 0.0, 0.0, 35_000.0, RiskLevel.NO_TRAVEL, RiskDriver.LOAD_RULE),
        (50.0, 0.0, 0.0, 30_000.0, RiskLevel.SEVERE, RiskDriver.WIND),
        (40.0, 0.0, 0.0, 45_000.0, RiskLevel.SEVERE, RiskDriver.LOAD_RULE),
        (40.0, 0.0, 0.0, 40_000.0, RiskLevel.HIGH, RiskDriver.WIND),
        (56.0, 0.0, 0.0, 0.0, RiskLevel.NO_TRAVEL, RiskDriver.WIND),
        (30.0, 0.60, 0.0, 10_000.0, RiskLevel.SEVERE, RiskDriver.RAIN),
        (20.0, 0.25, 0.0, 10_000.0, RiskLevel.HIGH, RiskDriver.RAIN),
        (10.0, 1.00, 0.0, 10_000.0, RiskLevel.SEVERE, RiskDriver.RAIN),
        (10.0, 1.01, 0.0, 10_000.0, RiskLevel.NO_TRAVEL, RiskDriver.RAIN),
        (10.0, 0.0, 3.00, 10_000.0, RiskLevel.SEVERE, RiskDriver.SNOW),
        (10.0, 0.0, 3.01, 10_000.0, RiskLevel.NO_TRAVEL, RiskDriver.SNOW),
    ],
)
def test_assess_worked_examples_table_matches_architecture_spec(
    wind: float,
    rain: float,
    snow: float,
    load: float,
    expected_level: RiskLevel,
    expected_driver: RiskDriver,
) -> None:
    sample = WeatherSample(wind_mph=wind, rain_in_hr=rain, snow_in_hr=snow)
    res = assess(sample, load)
    assert res.level == expected_level
    assert res.driver == expected_driver
    if expected_driver == RiskDriver.LOAD_RULE:
        assert res.load_rule_applied is True
    else:
        assert res.load_rule_applied is False


def test_assess_load_boundary_30000_vs_30001_lb_elevates_to_no_travel() -> None:
    sample = WeatherSample(wind_mph=50.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res_exact = assess(sample, 30_000.0)
    assert res_exact.level == RiskLevel.SEVERE
    assert res_exact.driver == RiskDriver.WIND
    assert res_exact.load_rule_applied is False

    res_over = assess(sample, 30_001.0)
    assert res_over.level == RiskLevel.NO_TRAVEL
    assert res_over.driver == RiskDriver.LOAD_RULE
    assert res_over.load_rule_applied is True


def test_assess_load_boundary_40000_vs_40001_lb_elevates_to_severe() -> None:
    sample = WeatherSample(wind_mph=40.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res_exact = assess(sample, 40_000.0)
    assert res_exact.level == RiskLevel.HIGH
    assert res_exact.driver == RiskDriver.WIND
    assert res_exact.load_rule_applied is False

    res_over = assess(sample, 40_001.0)
    assert res_over.level == RiskLevel.SEVERE
    assert res_over.driver == RiskDriver.LOAD_RULE
    assert res_over.load_rule_applied is True


def test_assess_wind_under_35_with_heavy_load_stays_moderate() -> None:
    sample = WeatherSample(wind_mph=34.9, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(sample, 100_000.0)
    assert res.level == RiskLevel.MODERATE
    assert res.driver == RiskDriver.WIND
    assert res.load_rule_applied is False


def test_assess_heavy_load_with_severe_rain_or_snow_changes_nothing() -> None:
    rain_sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.60, snow_in_hr=0.0)
    rain_res = assess(rain_sample, 80_000.0)
    assert rain_res.level == RiskLevel.SEVERE
    assert rain_res.driver == RiskDriver.RAIN
    assert rain_res.load_rule_applied is False

    snow_sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=2.50)
    snow_res = assess(snow_sample, 80_000.0)
    assert snow_res.level == RiskLevel.SEVERE
    assert snow_res.driver == RiskDriver.SNOW
    assert snow_res.load_rule_applied is False


def test_assess_load_rule_never_lowers_level_when_table_is_severe() -> None:
    # Rain is Severe (0.60), wind is High (40.0), load is 45,000 (load rule would give Severe)
    sample = WeatherSample(wind_mph=40.0, rain_in_hr=0.60, snow_in_hr=0.0)
    res = assess(sample, 45_000.0)
    assert res.level == RiskLevel.SEVERE
    assert res.table_level == RiskLevel.SEVERE
    # Load rule did not raise the level above table_level, so driver is RAIN, not LOAD_RULE
    assert res.driver == RiskDriver.RAIN
    assert res.load_rule_applied is False


def test_assess_driver_tie_order_prefers_wind_over_rain_over_snow() -> None:
    # All conditions are Moderate
    all_moderate = WeatherSample(wind_mph=25.0, rain_in_hr=0.10, snow_in_hr=0.5)
    res1 = assess(all_moderate, 10_000.0)
    assert res1.driver == RiskDriver.WIND

    # Rain and snow Moderate, wind Low
    rain_snow_moderate = WeatherSample(wind_mph=10.0, rain_in_hr=0.10, snow_in_hr=0.5)
    res2 = assess(rain_snow_moderate, 10_000.0)
    assert res2.driver == RiskDriver.RAIN

    # Snow Moderate, wind Low, rain Low
    snow_moderate = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.5)
    res3 = assess(snow_moderate, 10_000.0)
    assert res3.driver == RiskDriver.SNOW


def test_describe_low_wind_returns_expected_string() -> None:
    sample = WeatherSample(wind_mph=12.4, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(sample, 20_000.0)
    assert describe(sample, 20_000.0, res) == "Wind 12.4 mph is Low."


def test_describe_severe_rain_returns_expected_string() -> None:
    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.60, snow_in_hr=0.0)
    res = assess(sample, 10_000.0)
    assert describe(sample, 10_000.0, res) == "Rain 0.60 in/hr is Severe."


def test_describe_load_rule_elevation_to_severe_returns_expected_string() -> None:
    sample = WeatherSample(wind_mph=40.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(sample, 45_000.0)
    assert (
        describe(sample, 45_000.0, res)
        == "Wind 40.0 mph is High; load 45,000 lb over 40,000 lb makes it Severe."
    )


def test_describe_load_rule_elevation_to_no_travel_returns_expected_string() -> None:
    sample = WeatherSample(wind_mph=50.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(sample, 35_000.0)
    assert (
        describe(sample, 35_000.0, res)
        == "Wind 50.0 mph is Severe; load 35,000 lb over 30,000 lb makes it No Travel."
    )


def test_describe_mixed_conditions_names_driving_condition_only() -> None:
    sample = WeatherSample(wind_mph=20.0, rain_in_hr=0.60, snow_in_hr=0.10)
    res = assess(sample, 10_000.0)
    assert describe(sample, 10_000.0, res) == "Rain 0.60 in/hr is Severe."


def test_describe_snow_driver_returns_expected_string() -> None:
    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=3.01)
    res = assess(sample, 10_000.0)
    assert describe(sample, 10_000.0, res) == "Snow 3.01 in/hr is No Travel."


@pytest.mark.parametrize("invalid_load", [-1.0, float("nan"), float("inf")])
def test_describe_invalid_load_raises_value_error(invalid_load: float) -> None:
    sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(sample, 10_000.0)
    with pytest.raises(ValueError):
        describe(sample, invalid_load, res)


@pytest.mark.parametrize(
    "invalid_sample",
    [
        WeatherSample(wind_mph=-1.0, rain_in_hr=0.0, snow_in_hr=0.0),
        WeatherSample(wind_mph=10.0, rain_in_hr=-0.1, snow_in_hr=0.0),
        WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=-0.1),
        WeatherSample(wind_mph=float("nan"), rain_in_hr=0.0, snow_in_hr=0.0),
        WeatherSample(wind_mph=10.0, rain_in_hr=float("nan"), snow_in_hr=0.0),
        WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=float("nan")),
        WeatherSample(wind_mph=float("inf"), rain_in_hr=0.0, snow_in_hr=0.0),
        WeatherSample(wind_mph=10.0, rain_in_hr=float("inf"), snow_in_hr=0.0),
        WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=float("inf")),
    ],
)
def test_describe_invalid_weather_sample_raises_value_error(invalid_sample: WeatherSample) -> None:
    valid_sample = WeatherSample(wind_mph=10.0, rain_in_hr=0.0, snow_in_hr=0.0)
    res = assess(valid_sample, 10_000.0)
    with pytest.raises(ValueError):
        describe(invalid_sample, 10_000.0, res)
