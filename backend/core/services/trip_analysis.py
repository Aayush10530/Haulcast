"""Trip analysis service orchestrating routing, weather, risk scoring, and ranking."""

import datetime
import time
from collections.abc import Callable

from core.domain import geometry, ranking, rules_config, sampling, scoring, timezones
from core.domain.errors import BeyondForecastHorizonError, DepartureOutOfWindowError
from core.domain.grid import snap_to_cell
from core.domain.timeline import etas_for_checkpoints
from core.domain.types import (
    AnalyzedRoute,
    AssessedCheckpoint,
    Checkpoint,
    GridCell,
    RankingInput,
    RouteSummary,
    SelectedRoute,
    TripAnalysis,
    TripAnalysisMeta,
    TripRequest,
    TripRequestEcho,
    Warning,
)
from core.providers.base import ProviderBadResponse, WeatherProvider
from core.services.route_selection import RouteSelectionService


class TripAnalysisService:
    """Orchestrates route selection, weather alignment, scoring, and ranking for trips."""

    def __init__(
        self,
        route_selection: RouteSelectionService,
        weather: WeatherProvider,
        clock: Callable[[], datetime.datetime] = lambda: datetime.datetime.now(datetime.UTC),
    ) -> None:
        self.route_selection = route_selection
        self.weather = weather
        self.clock = clock

    def analyze(self, request: TripRequest) -> TripAnalysis:
        """Execute complete trip analysis from request to ranked routes and recommendation."""
        t0 = time.perf_counter()

        # 1. Resolve origin timezone, convert local departure to UTC, and validate window
        origin_tz = self.weather.get_timezone(request.origin.coordinate)
        departure_utc = timezones.local_to_utc(request.departure_local, origin_tz)
        try:
            timezones.validate_departure_window(departure_utc, now_utc=self.clock())
        except DepartureOutOfWindowError as e:
            raise DepartureOutOfWindowError(
                str(e),
                allowed_from=e.allowed_from,
                allowed_to=e.allowed_to,
                origin_tz=origin_tz,
            ) from e

        # 2. Fetch diverse candidate routes via route selection service (cached)
        selection_result = self.route_selection.get_routes(
            origin=request.origin.coordinate,
            destination=request.destination.coordinate,
        )
        selected_routes = selection_result.routes

        # 3. Resolve interval from longest route's distance
        longest_miles = max(sr.raw.distance_miles for sr in selected_routes)
        interval_miles = sampling.resolve_interval(
            mode=request.interval_mode,
            manual_miles=request.manual_interval,
            longest_route_miles=longest_miles,
        )

        # 4. Per route: checkpoints, timeline check, ETAs
        routes_prep: list[tuple[SelectedRoute, list[Checkpoint], list[datetime.datetime]]] = []
        for sr in selected_routes:
            raw = sr.raw
            timeline = raw.timeline
            if abs(timeline.total_miles - raw.distance_miles) > 0.01:
                raise ProviderBadResponse(
                    f"Route {sr.route_id} timeline total miles {timeline.total_miles:.3f} "
                    f"deviates from route distance {raw.distance_miles:.3f} by > 0.01 mi"
                )
            cum = geometry.cumulative_miles(raw.polyline, raw.distance_miles)
            checkpoints = sampling.build_checkpoints(raw.polyline, cum, interval_miles)
            etas = etas_for_checkpoints(departure_utc, timeline, checkpoints)
            routes_prep.append((sr, checkpoints, etas))

        # 5. Collect unique GridCells from all checkpoints and call weather.get_series once
        unique_cells: list[GridCell] = list(
            dict.fromkeys(snap_to_cell(cp.coordinate) for _, cps, _ in routes_prep for cp in cps)
        )
        weather_map = self.weather.get_series(unique_cells)

        all_etas = [eta for _, _, etas in routes_prep for eta in etas]

        if not weather_map:
            raise BeyondForecastHorizonError(
                "Weather series data unavailable for all route cells",
                last_forecast_time=departure_utc,
            )

        last_forecast_time = max(
            datetime.datetime.fromtimestamp(
                s.wind_mph.start_epoch
                + (len(s.wind_mph.values) - 1) * rules_config.SECONDS_PER_HOUR,
                tz=datetime.UTC,
            )
            for s in weather_map.values()
        )

        # Horizon check: if any ETA is beyond the series window for ALL cells
        if any(eta > last_forecast_time for eta in all_etas):
            raise BeyondForecastHorizonError(
                f"Trip arrival time exceeds available forecast horizon "
                f"(last available: {last_forecast_time.isoformat()})",
                last_forecast_time=last_forecast_time,
            )

        # 6. Per checkpoint: assess against weather series
        # 7. Per route: summarize route
        analyzed_data: list[tuple[SelectedRoute, tuple[AssessedCheckpoint, ...], RouteSummary]] = []
        all_assessed_cps: list[AssessedCheckpoint] = []
        for sr, checkpoints, etas in routes_prep:
            assessed_cps: list[AssessedCheckpoint] = []
            for cp, eta in zip(checkpoints, etas, strict=True):
                cell = snap_to_cell(cp.coordinate)
                series = weather_map.get(cell)
                ac = scoring.assess_checkpoint(
                    checkpoint=cp,
                    eta_utc=eta,
                    series=series,
                    load_weight_lb=float(request.load_weight_lb),
                )
                assessed_cps.append(ac)
                all_assessed_cps.append(ac)

            summary = scoring.summarize_route(
                assessed=tuple(assessed_cps),
                distance_miles=sr.raw.distance_miles,
                duration_seconds=sr.raw.duration_seconds,
            )
            analyzed_data.append((sr, tuple(assessed_cps), summary))

        if all(ac.sample is None for ac in all_assessed_cps):
            raise BeyondForecastHorizonError(
                "All weather cells unavailable for trip corridor",
                last_forecast_time=last_forecast_time,
            )

        # 8. ranking.rank_routes
        ranking_inputs = [
            RankingInput(route_id=sr.route_id, label=sr.label, summary=summary)
            for sr, _, summary in analyzed_data
        ]
        recommendation = ranking.rank_routes(ranking_inputs)
        ranked_lookup = {r.route_id: r for r in recommendation.ranked}

        # 9. Warnings
        warnings_list: list[Warning] = list(selection_result.warnings)
        total_unavailable = sum(summary.unavailable_checkpoints for _, _, summary in analyzed_data)
        if total_unavailable > 0:
            warnings_list.append(
                Warning(
                    code="WEATHER_UNAVAILABLE_SOME",
                    message=f"{total_unavailable} checkpoint(s) have unavailable weather data.",
                )
            )
        if recommendation.no_safe_route:
            warnings_list.append(
                Warning(
                    code="NO_SAFE_ROUTE",
                    message="No safe route available under current weather conditions.",
                )
            )

        # Assemble AnalyzedRoute objects
        analyzed_routes: list[AnalyzedRoute] = []
        for sr, assessed_cps, summary in analyzed_data:
            r_info = ranked_lookup[sr.route_id]
            simplified = geometry.simplify(sr.raw.polyline, tolerance_m=50.0)
            analyzed_routes.append(
                AnalyzedRoute(
                    route_id=sr.route_id,
                    label=sr.label,
                    raw=sr.raw,
                    checkpoints=assessed_cps,
                    summary=summary,
                    rank=r_info.rank,
                    delta_vs_fastest_seconds=r_info.delta_vs_fastest_seconds,
                    is_recommended=(sr.route_id == recommendation.route_id),
                    display_polyline=tuple(simplified),
                    via_summary=sr.raw.via_summary,
                )
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        echo = TripRequestEcho(
            origin=request.origin,
            destination=request.destination,
            departure_utc=departure_utc,
            departure_local=request.departure_local,
            origin_tz=origin_tz,
            load_weight_lb=request.load_weight_lb,
            interval_miles=interval_miles,
            interval_mode=request.interval_mode,
        )
        meta = TripAnalysisMeta(
            weather_cells=len(unique_cells),
            route_count=len(analyzed_routes),
            elapsed_ms=elapsed_ms,
        )

        return TripAnalysis(
            request=echo,
            routes=tuple(analyzed_routes),
            recommendation=recommendation,
            warnings=tuple(warnings_list),
            meta=meta,
        )
