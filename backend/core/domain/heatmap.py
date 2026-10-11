"""Domain heatmap models and frame aggregation."""

import datetime
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from core.domain import risk, rules_config, weather_align
from core.domain.types import GridCell, WeatherSeries


@dataclass(frozen=True, slots=True)
class HeatmapFrame:
    """A single hourly forecast slice across all corridor grid cells."""

    offset_hours: int
    time_utc: datetime.datetime
    overall: tuple[int | None, ...]
    wind: tuple[int | None, ...]
    rain: tuple[int | None, ...]
    snow: tuple[int | None, ...]


@dataclass(frozen=True, slots=True)
class Heatmap:
    """Complete 49-frame corridor forecast heatmap across grid cells."""

    cells: tuple[GridCell, ...]
    start_utc: datetime.datetime
    frames: tuple[HeatmapFrame, ...]


def build_heatmap(
    cells: Sequence[GridCell],
    series_by_cell: Mapping[GridCell, WeatherSeries],
    departure_utc: datetime.datetime,
    load_weight_lb: float,
) -> Heatmap:
    """Build a 49-frame corridor heatmap from departure time up to +48 hours.

    t_k = floor_to_hour(departure UTC) + k hours for k in 0..48.
    For each cell at t_k, weather is sampled via weather_align.sample_at and assessed
    via risk.assess.
    - overall: risk level including payload weight rules (0-4 or None)
    - wind, rain, snow: per-condition risk levels without payload weight rules (0-4 or None)
    """
    if departure_utc.tzinfo is None or departure_utc.tzinfo.utcoffset(departure_utc) is None:
        raise ValueError(f"departure_utc must be timezone-aware UTC datetime, got {departure_utc}")

    start_utc = departure_utc.replace(minute=0, second=0, microsecond=0)
    cells_tuple = tuple(cells)

    frames: list[HeatmapFrame] = []
    for k in range(rules_config.HEATMAP_HOURS + 1):
        t_k = start_utc + datetime.timedelta(hours=k)

        overall_list: list[int | None] = []
        wind_list: list[int | None] = []
        rain_list: list[int | None] = []
        snow_list: list[int | None] = []

        for cell in cells_tuple:
            series = series_by_cell.get(cell)
            if series is None:
                overall_list.append(None)
                wind_list.append(None)
                rain_list.append(None)
                snow_list.append(None)
                continue

            sample = weather_align.sample_at(series, t_k)
            if sample is None:
                overall_list.append(None)
                wind_list.append(None)
                rain_list.append(None)
                snow_list.append(None)
                continue

            assessment = risk.assess(sample, load_weight_lb)
            overall_list.append(int(assessment.level))
            wind_list.append(int(assessment.per_condition_levels.wind))
            rain_list.append(int(assessment.per_condition_levels.rain))
            snow_list.append(int(assessment.per_condition_levels.snow))

        frames.append(
            HeatmapFrame(
                offset_hours=k,
                time_utc=t_k,
                overall=tuple(overall_list),
                wind=tuple(wind_list),
                rain=tuple(rain_list),
                snow=tuple(snow_list),
            )
        )

    return Heatmap(
        cells=cells_tuple,
        start_utc=start_utc,
        frames=tuple(frames),
    )
