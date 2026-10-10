import datetime
import math

from core.domain import rules_config
from core.domain.types import HourlySeries, WeatherSample, WeatherSeries


def _is_valid_value(val: float | None) -> bool:
    """Check if raw measurement value is valid (not None, finite, and non-negative)."""
    return val is not None and math.isfinite(val) and val >= 0.0


def wind_at(series: HourlySeries, t: datetime.datetime) -> float | None:
    """Interpolate wind speed at time t from an hourly series.

    Returns None if t is outside the series range or if required points are missing.
    On exact hour markers (frac == 0), only the current hour value is required.
    """
    if t.tzinfo is None or t.tzinfo.utcoffset(t) is None:
        raise ValueError(f"t must be a timezone-aware datetime, got {t}")

    t_epoch = t.timestamp()
    if t_epoch < series.start_epoch:
        return None

    idx = math.floor((t_epoch - series.start_epoch) / rules_config.SECONDS_PER_HOUR)
    if idx >= len(series.values):
        return None

    frac = (
        t_epoch - (series.start_epoch + idx * rules_config.SECONDS_PER_HOUR)
    ) / rules_config.SECONDS_PER_HOUR

    if math.isclose(frac, 0.0, abs_tol=1e-9):
        val = series.values[idx]
        return val if _is_valid_value(val) else None

    # frac > 0: both current and next hour must be present and valid
    if idx + 1 >= len(series.values):
        return None

    v0 = series.values[idx]
    v1 = series.values[idx + 1]
    if not _is_valid_value(v0) or not _is_valid_value(v1):
        return None

    return v0 + frac * (v1 - v0)


def precip_at(series: HourlySeries, t: datetime.datetime) -> float | None:
    """Lookup precipitation (rain or snow) rate at time t from an hourly series.

    Returns the value at index idx + 1 (the 1-hour accumulation bucket ending at that time).
    Returns None if out of bounds or if the bucket value is missing.
    Times earlier than start_epoch return None even though the first bucket would cover the
    preceding hour; harmless because fetch windows start 3 hours in the past.
    """
    if t.tzinfo is None or t.tzinfo.utcoffset(t) is None:
        raise ValueError(f"t must be a timezone-aware datetime, got {t}")

    t_epoch = t.timestamp()
    if t_epoch < series.start_epoch:
        return None

    idx = math.floor((t_epoch - series.start_epoch) / rules_config.SECONDS_PER_HOUR)
    target_idx = idx + 1
    if target_idx < 0 or target_idx >= len(series.values):
        return None

    val = series.values[target_idx]
    return val if _is_valid_value(val) else None


def sample_at(series: WeatherSeries, t: datetime.datetime) -> WeatherSample | None:
    """Sample and round weather conditions at time t.

    Returns None if any of wind, rain, or snow is missing or unavailable.
    Rounding acts on the binary float value and is deterministic.
    """
    wind = wind_at(series.wind_mph, t)
    rain = precip_at(series.rain_in_hr, t)
    snow = precip_at(series.snow_in_hr, t)

    if wind is None or rain is None or snow is None:
        return None

    return WeatherSample(
        wind_mph=round(wind, rules_config.WIND_DECIMALS),
        rain_in_hr=round(rain, rules_config.PRECIP_DECIMALS),
        snow_in_hr=round(snow, rules_config.PRECIP_DECIMALS),
    )
