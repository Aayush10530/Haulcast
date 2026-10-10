import datetime
import zoneinfo

import pytest

from core.domain.types import HourlySeries, WeatherSample, WeatherSeries
from core.domain.weather_align import precip_at, sample_at, wind_at

# Epoch base: 2026-10-15 12:00:00 UTC
EPOCH_12_00 = 1_792_065_600


def _time_utc(hour: int, minute: int = 0, second: int = 0) -> datetime.datetime:
    return datetime.datetime(2026, 10, 15, hour, minute, second, tzinfo=datetime.UTC)


def test_wind_at_on_the_hour_exact_value_even_when_next_hour_missing() -> None:
    # Series starts at 14:00 (index 0). Next hour (index 1) is None.
    series = HourlySeries(start_epoch=EPOCH_12_00 + 7200, values=(15.0, None))
    t_14 = _time_utc(14, 0, 0)
    assert wind_at(series, t_14) == 15.0


def test_wind_at_halfway_and_one_third_interpolation_returns_expected_mph() -> None:
    # 14:00 has 10.0, 15:00 has 22.0
    series = HourlySeries(start_epoch=EPOCH_12_00 + 7200, values=(10.0, 22.0))

    # One-third (14:20): 10.0 + (1/3) * (22.0 - 10.0) = 14.0
    t_14_20 = _time_utc(14, 20, 0)
    assert wind_at(series, t_14_20) == pytest.approx(14.0)

    # Halfway (14:30): 10.0 + 0.5 * 12.0 = 16.0
    t_14_30 = _time_utc(14, 30, 0)
    assert wind_at(series, t_14_30) == pytest.approx(16.0)


def test_wind_at_missing_neighbour_with_fraction_above_zero_returns_none() -> None:
    # 14:00 is valid, 15:00 is None
    series1 = HourlySeries(start_epoch=EPOCH_12_00 + 7200, values=(10.0, None))
    assert wind_at(series1, _time_utc(14, 30, 0)) is None

    # 14:00 is None, 15:00 is valid
    series2 = HourlySeries(start_epoch=EPOCH_12_00 + 7200, values=(None, 20.0))
    assert wind_at(series2, _time_utc(14, 30, 0)) is None


def test_wind_at_before_start_and_after_end_returns_none() -> None:
    series = HourlySeries(start_epoch=EPOCH_12_00 + 7200, values=(10.0, 20.0))
    # Before start: 13:59:59
    assert wind_at(series, _time_utc(13, 59, 59)) is None
    # Just after end: 15:00:01
    assert wind_at(series, _time_utc(15, 0, 1)) is None
    # Far after end: 16:00:00 (idx >= len)
    assert wind_at(series, _time_utc(16, 0, 0)) is None


def test_wind_at_exactly_last_timestamp_returns_exact_value() -> None:
    # Series with 2 points: 14:00 (10.0) and 15:00 (20.0)
    series = HourlySeries(start_epoch=EPOCH_12_00 + 7200, values=(10.0, 20.0))
    assert wind_at(series, _time_utc(15, 0, 0)) == 20.0


def test_precip_at_bucket_rule_for_interior_and_boundary_times() -> None:
    # Series starts at 12:00:
    # index 0 (12:00): 0.10
    # index 1 (13:00): 0.20
    # index 2 (14:00): 0.30
    # index 3 (15:00): 0.40
    series = HourlySeries(start_epoch=EPOCH_12_00, values=(0.10, 0.20, 0.30, 0.40))

    # ETA 14:20 uses 15:00 value (index 3)
    assert precip_at(series, _time_utc(14, 20, 0)) == 0.40

    # ETA 14:00 exactly also uses 15:00 value (index 3)
    assert precip_at(series, _time_utc(14, 0, 0)) == 0.40

    # ETA 13:59:59 uses 14:00 value (index 2)
    assert precip_at(series, _time_utc(13, 59, 59)) == 0.30


def test_precip_at_before_start_and_after_end_returns_none() -> None:
    series = HourlySeries(start_epoch=EPOCH_12_00, values=(0.10, 0.20, 0.30))
    # Before start: 11:59:59
    assert precip_at(series, _time_utc(11, 59, 59)) is None
    # At index 2 (14:00), target_idx = 3 which is out of bounds (len is 3)
    assert precip_at(series, _time_utc(14, 0, 0)) is None


def test_precip_at_rain_and_snow_evaluated_independently() -> None:
    rain_series = HourlySeries(start_epoch=EPOCH_12_00, values=(0.0, 0.25, 0.50))
    snow_series = HourlySeries(start_epoch=EPOCH_12_00, values=(0.0, None, 1.50))

    # At 12:30, target_idx = 1
    assert precip_at(rain_series, _time_utc(12, 30, 0)) == 0.25
    assert precip_at(snow_series, _time_utc(12, 30, 0)) is None


def test_sample_at_any_missing_variable_returns_none() -> None:
    t = _time_utc(13, 0, 0)

    # Missing wind
    ws1 = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_12_00, (None, None)),
        rain_in_hr=HourlySeries(EPOCH_12_00, (0.0, 0.1)),
        snow_in_hr=HourlySeries(EPOCH_12_00, (0.0, 0.0)),
    )
    assert sample_at(ws1, t) is None

    # Missing rain
    ws2 = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_12_00, (10.0, 10.0)),
        rain_in_hr=HourlySeries(EPOCH_12_00, (0.0, None)),
        snow_in_hr=HourlySeries(EPOCH_12_00, (0.0, 0.0)),
    )
    assert sample_at(ws2, t) is None

    # Missing snow
    ws3 = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_12_00, (10.0, 10.0)),
        rain_in_hr=HourlySeries(EPOCH_12_00, (0.0, 0.1)),
        snow_in_hr=HourlySeries(EPOCH_12_00, (0.0, None)),
    )
    assert sample_at(ws3, t) is None


@pytest.mark.parametrize("invalid_raw", [None, float("nan"), float("inf"), float("-inf"), -0.01])
def test_weather_align_invalid_raw_values_count_as_missing(invalid_raw: float | None) -> None:
    series = HourlySeries(EPOCH_12_00, (invalid_raw, invalid_raw))
    t_12 = _time_utc(12, 0, 0)
    assert wind_at(series, t_12) is None
    assert precip_at(series, t_12) is None


def test_sample_at_rounding_cases_applies_deterministic_precision() -> None:
    # Wind 24.96 -> 25.0
    # Rain 0.096 -> 0.10
    # Snow 0.094 -> 0.09
    ws = WeatherSeries(
        tz_name="UTC",
        wind_mph=HourlySeries(EPOCH_12_00, (24.96, 24.96)),
        rain_in_hr=HourlySeries(EPOCH_12_00, (0.0, 0.096)),
        snow_in_hr=HourlySeries(EPOCH_12_00, (0.0, 0.094)),
    )
    sample = sample_at(ws, _time_utc(12, 0, 0))
    assert sample == WeatherSample(
        wind_mph=25.0,
        rain_in_hr=0.10,
        snow_in_hr=0.09,
    )


def test_weather_align_naive_datetime_raises_value_error() -> None:
    naive_dt = datetime.datetime(2026, 10, 15, 12, 0, 0)
    h_series = HourlySeries(EPOCH_12_00, (10.0, 20.0))
    w_series = WeatherSeries(
        tz_name="UTC",
        wind_mph=h_series,
        rain_in_hr=h_series,
        snow_in_hr=h_series,
    )

    with pytest.raises(ValueError, match="timezone-aware datetime"):
        wind_at(h_series, naive_dt)
    with pytest.raises(ValueError, match="timezone-aware datetime"):
        precip_at(h_series, naive_dt)
    with pytest.raises(ValueError, match="timezone-aware datetime"):
        sample_at(w_series, naive_dt)


def test_weather_align_non_utc_aware_datetime_matches_utc_equivalent() -> None:
    h_series = HourlySeries(EPOCH_12_00, (10.0, 22.0))
    w_series = WeatherSeries(
        tz_name="America/New_York",
        wind_mph=h_series,
        rain_in_hr=h_series,
        snow_in_hr=h_series,
    )

    # 12:20 UTC = 08:20 EDT (UTC-4)
    t_utc = _time_utc(12, 20, 0)
    t_ny = datetime.datetime(2026, 10, 15, 8, 20, 0, tzinfo=zoneinfo.ZoneInfo("America/New_York"))

    assert wind_at(h_series, t_ny) == wind_at(h_series, t_utc)
    assert precip_at(h_series, t_ny) == precip_at(h_series, t_utc)
    assert sample_at(w_series, t_ny) == sample_at(w_series, t_utc)


def test_weather_align_series_with_start_epoch_offset_by_half_hour_still_works() -> None:
    # start_epoch is 12:30 (EPOCH_12_00 + 1800)
    series = HourlySeries(start_epoch=EPOCH_12_00 + 1800, values=(10.0, 20.0))

    # Query 12:30 exactly (start) -> 10.0
    t_12_30 = _time_utc(12, 30, 0)
    assert wind_at(series, t_12_30) == 10.0

    # Query 13:00 (halfway) -> 15.0
    t_13_00 = _time_utc(13, 0, 0)
    assert wind_at(series, t_13_00) == pytest.approx(15.0)

    # Precip at 12:30 uses index 1 (13:30 value)
    assert precip_at(series, t_12_30) == 20.0


def test_hourly_series_list_converted_to_tuple() -> None:
    series = HourlySeries(start_epoch=EPOCH_12_00, values=[10.0, 20.0])  # type: ignore[arg-type]
    assert isinstance(series.values, tuple)
    assert series.values == (10.0, 20.0)


def test_hourly_series_empty_values_raises_value_error() -> None:
    with pytest.raises(ValueError, match="HourlySeries values cannot be empty"):
        HourlySeries(start_epoch=EPOCH_12_00, values=())


def test_weather_series_mismatched_start_epoch_raises_value_error() -> None:
    s1 = HourlySeries(start_epoch=EPOCH_12_00, values=(10.0, 20.0))
    s2 = HourlySeries(start_epoch=EPOCH_12_00 + 3600, values=(10.0, 20.0))

    with pytest.raises(ValueError, match="matching start_epoch"):
        WeatherSeries(
            tz_name="UTC",
            wind_mph=s1,
            rain_in_hr=s2,
            snow_in_hr=s1,
        )


def test_weather_series_mismatched_lengths_raises_value_error() -> None:
    s1 = HourlySeries(start_epoch=EPOCH_12_00, values=(10.0, 20.0))
    s2 = HourlySeries(start_epoch=EPOCH_12_00, values=(10.0, 20.0, 30.0))

    with pytest.raises(ValueError, match="matching lengths"):
        WeatherSeries(
            tz_name="UTC",
            wind_mph=s1,
            rain_in_hr=s2,
            snow_in_hr=s1,
        )
