"""Heatmap service generating corridor cells and building 49-frame risk heatmaps."""

import datetime
import zoneinfo
from collections.abc import Callable
from dataclasses import dataclass

from core.domain import rules_config
from core.domain.corridor import generate_corridor_cells
from core.domain.errors import BeyondForecastHorizonError
from core.domain.heatmap import Heatmap, build_heatmap
from core.domain.types import TripRequest
from core.providers.base import WeatherProvider
from core.services.departure import resolve_departure
from core.services.route_selection import RouteSelectionService


@dataclass(frozen=True, slots=True)
class HeatmapResult:
    """Result returned by HeatmapService carrying heatmap domain model and local timings."""

    heatmap: Heatmap
    start_local: str
    origin_tz: str
    frame_times_local: tuple[str, ...]


class HeatmapService:
    """Orchestrates corridor grid generation and hourly risk heatmap building."""

    def __init__(
        self,
        route_selection: RouteSelectionService,
        weather: WeatherProvider,
        clock: Callable[[], datetime.datetime] = lambda: datetime.datetime.now(datetime.UTC),
    ) -> None:
        self.route_selection = route_selection
        self.weather = weather
        self.clock = clock

    def build(self, request: TripRequest) -> HeatmapResult:
        """Build a 49-frame corridor weather heatmap for a given trip request."""
        # 1. Resolve origin timezone, convert local departure to UTC, and validate window
        origin_tz, departure_utc = resolve_departure(
            origin_coord=request.origin.coordinate,
            departure_local=request.departure_local,
            weather=self.weather,
            clock=self.clock,
        )

        # 2. Fetch candidate routes (uses cache from trip analysis if already called)
        selection_result = self.route_selection.get_routes(
            origin=request.origin.coordinate,
            destination=request.destination.coordinate,
        )
        routes_polylines = [sr.raw.polyline for sr in selection_result.routes]
        routes_miles = [sr.raw.distance_miles for sr in selection_result.routes]

        # 3. Generate corridor grid cells (<= 250)
        cells = generate_corridor_cells(routes_polylines, routes_miles)

        # 4. Fetch weather series once for all cells (hits shared weather cache)
        weather_map = self.weather.get_series(cells)

        # 5. Build 49 hourly heatmap frames
        heatmap = build_heatmap(
            cells=cells,
            series_by_cell=weather_map,
            departure_utc=departure_utc,
            load_weight_lb=float(request.load_weight_lb),
        )

        # 6. Horizon check: if every cell in frame 0 is None, raise BeyondForecastHorizonError
        if not heatmap.frames or all(val is None for val in heatmap.frames[0].overall):
            last_forecast = max(
                (
                    datetime.datetime.fromtimestamp(
                        s.wind_mph.start_epoch
                        + (len(s.wind_mph.values) - 1) * rules_config.SECONDS_PER_HOUR,
                        tz=datetime.UTC,
                    )
                    for s in weather_map.values()
                ),
                default=departure_utc,
            )
            raise BeyondForecastHorizonError(
                "Forecast data unavailable for heatmap corridor",
                last_forecast_time=last_forecast,
            )

        # 7. Compute origin-local ISO times
        tz_obj = zoneinfo.ZoneInfo(origin_tz)
        start_local = heatmap.start_utc.astimezone(tz_obj).isoformat()
        frame_times_local = tuple(f.time_utc.astimezone(tz_obj).isoformat() for f in heatmap.frames)

        return HeatmapResult(
            heatmap=heatmap,
            start_local=start_local,
            origin_tz=origin_tz,
            frame_times_local=frame_times_local,
        )
