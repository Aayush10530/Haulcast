"""Tests for pure domain heatmap building and frame risk aggregation."""

import datetime

from core.domain.heatmap import build_heatmap
from core.domain.types import GridCell, HourlySeries, WeatherSeries


def _build_series(
    start_epoch: int,
    num_hours: int = 60,
    hour5_wind: float = 40.0,
) -> WeatherSeries:
    """Build a synthetic WeatherSeries where hour 5 has specific wind conditions."""
    wind_vals = [10.0] * num_hours
    if num_hours > 5:
        wind_vals[5] = hour5_wind

    rain_vals = [0.0] * num_hours
    snow_vals = [0.0] * num_hours

    return WeatherSeries(
        tz_name="America/Chicago",
        wind_mph=HourlySeries(start_epoch=start_epoch, values=tuple(wind_vals)),
        rain_in_hr=HourlySeries(start_epoch=start_epoch, values=tuple(rain_vals)),
        snow_in_hr=HourlySeries(start_epoch=start_epoch, values=tuple(snow_vals)),
    )


def test_heatmap_two_cells_payload_rules_missing_data_and_forty_nine_frames() -> None:
    # Anchor at a clean hour boundary: 2026-10-12 12:00:00 UTC
    start_epoch = 1791806400
    dep_utc = datetime.datetime.fromtimestamp(start_epoch, tz=datetime.UTC) + datetime.timedelta(
        minutes=30
    )

    cell_a = GridCell(lat_index=350, lon_index=-1000)
    cell_b = GridCell(lat_index=351, lon_index=-1000)  # Missing series

    series_a = _build_series(start_epoch=start_epoch, num_hours=60, hour5_wind=40.0)
    series_by_cell = {cell_a: series_a}

    # 1. Test with 45,000 lb load: at hour 5, overall is Severe (3) and wind is High (2)
    hm_heavy = build_heatmap(
        cells=[cell_a, cell_b],
        series_by_cell=series_by_cell,
        departure_utc=dep_utc,
        load_weight_lb=45000.0,
    )

    assert len(hm_heavy.frames) == 49
    assert hm_heavy.cells == (cell_a, cell_b)
    assert hm_heavy.start_utc == datetime.datetime.fromtimestamp(start_epoch, tz=datetime.UTC)

    # Offsets 0 to 48, time_utc increments by 1 hour
    for k, f in enumerate(hm_heavy.frames):
        assert f.offset_hours == k
        assert f.time_utc == hm_heavy.start_utc + datetime.timedelta(hours=k)
        assert len(f.overall) == 2
        assert len(f.wind) == 2
        assert len(f.rain) == 2
        assert len(f.snow) == 2

    frame5_heavy = hm_heavy.frames[5]
    # cell_a: overall = Severe (3), wind = High (2)
    assert frame5_heavy.overall[0] == 3
    assert frame5_heavy.wind[0] == 2
    assert frame5_heavy.rain[0] == 0
    assert frame5_heavy.snow[0] == 0

    # cell_b: missing series gives None across all layers
    assert frame5_heavy.overall[1] is None
    assert frame5_heavy.wind[1] is None
    assert frame5_heavy.rain[1] is None
    assert frame5_heavy.snow[1] is None

    # 2. Test with 10,000 lb load: at hour 5, both overall and wind are High (2)
    hm_light = build_heatmap(
        cells=[cell_a, cell_b],
        series_by_cell=series_by_cell,
        departure_utc=dep_utc,
        load_weight_lb=10000.0,
    )

    frame5_light = hm_light.frames[5]
    assert frame5_light.overall[0] == 2
    assert frame5_light.wind[0] == 2
    assert frame5_light.overall[1] is None


def test_heatmap_missing_or_incomplete_data_returns_none() -> None:
    start_epoch = 1791806400
    dep_utc = datetime.datetime.fromtimestamp(start_epoch, tz=datetime.UTC)

    cell = GridCell(lat_index=350, lon_index=-1000)

    # Series with only 3 hours of data
    short_series = _build_series(start_epoch=start_epoch, num_hours=3)
    hm = build_heatmap(
        cells=[cell],
        series_by_cell={cell: short_series},
        departure_utc=dep_utc,
        load_weight_lb=20000.0,
    )

    # Frame 0 to 2 have data
    assert hm.frames[0].overall[0] is not None
    # Frame 10 is beyond series horizon -> None
    assert hm.frames[10].overall[0] is None
    assert hm.frames[10].wind[0] is None
    assert hm.frames[10].rain[0] is None
    assert hm.frames[10].snow[0] is None


def test_heatmap_naive_departure_raises_value_error() -> None:
    import pytest

    cell = GridCell(lat_index=350, lon_index=-1000)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_heatmap([cell], {}, datetime.datetime(2026, 10, 12, 12, 0), 20000.0)
