"""Trip analysis service orchestrating routing, weather, risk scoring, and ranking."""

import datetime
import time
from collections.abc import Callable

from core.domain import geometry, ranking, rules_config, sampling, scoring
from core.domain.errors import BeyondForecastHorizonError
from core.domain.grid import snap_to_cell
from core.domain.timeline import etas_for_checkpoints
from core.domain.types import (
    AnalyzedRoute,
    AssessedCheckpoint,
    Checkpoint,
    GridCell,
    RankingInput,
    Recommendation,
    RouteSummary,
    SelectedRoute,
    TripAnalysis,
    TripAnalysisMeta,
    TripRequest,
    TripRequestEcho,
    Warning,
    WeatherSeries,
)
from core.providers.base import ProviderBadResponse, WeatherProvider
from core.services.departure import resolve_departure
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

        origin_tz, departure_utc = self._resolve_departure(request)
        selected_routes, routing_ms, route_warnings = self._fetch_candidate_routes(request)
        interval_miles, routes_prep = self._prepare_routes(
            selected_routes, request, departure_utc
        )
        weather_map, weather_ms, unique_cells, last_forecast_time = (
            self._fetch_and_validate_weather(routes_prep, departure_utc)
        )
        analyzed_data = self._assess_routes(
            routes_prep, weather_map, float(request.load_weight_lb), last_forecast_time
        )
        recommendation = self._rank_routes(analyzed_data)
        warnings_tuple = self._compile_warnings(
            route_warnings, analyzed_data, recommendation.no_safe_route
        )
        analyzed_routes = self._assemble_analyzed_routes(analyzed_data, recommendation)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        in_process_ms = max(0.0, elapsed_ms - routing_ms - weather_ms)

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
            routing_ms=routing_ms,
            weather_ms=weather_ms,
            in_process_ms=in_process_ms,
        )

        return TripAnalysis(
            request=echo,
            routes=analyzed_routes,
            recommendation=recommendation,
            warnings=warnings_tuple,
            meta=meta,
        )

    def _resolve_departure(self, request: TripRequest) -> tuple[str, datetime.datetime]:
        return resolve_departure(
            origin_coord=request.origin.coordinate,
            departure_local=request.departure_local,
            weather=self.weather,
            clock=self.clock,
        )

    def _fetch_candidate_routes(
        self, request: TripRequest
    ) -> tuple[tuple[SelectedRoute, ...], float, tuple[Warning, ...]]:
        t_route_0 = time.perf_counter()
        selection_result = self.route_selection.get_routes(
            origin=request.origin.coordinate,
            destination=request.destination.coordinate,
        )
        routing_ms = (time.perf_counter() - t_route_0) * 1000.0
        return selection_result.routes, routing_ms, selection_result.warnings

    def _prepare_routes(
        self,
        selected_routes: tuple[SelectedRoute, ...],
        request: TripRequest,
        departure_utc: datetime.datetime,
    ) -> tuple[float, list[tuple[SelectedRoute, list[Checkpoint], list[datetime.datetime]]]]:
        longest_miles = max(sr.raw.distance_miles for sr in selected_routes)
        interval_miles = sampling.resolve_interval(
            mode=request.interval_mode,
            manual_miles=request.manual_interval,
            longest_route_miles=longest_miles,
        )
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
        return interval_miles, routes_prep

    def _fetch_and_validate_weather(
        self,
        routes_prep: list[tuple[SelectedRoute, list[Checkpoint], list[datetime.datetime]]],
        departure_utc: datetime.datetime,
    ) -> tuple[dict[GridCell, WeatherSeries], float, list[GridCell], datetime.datetime]:
        unique_cells: list[GridCell] = list(
            dict.fromkeys(snap_to_cell(cp.coordinate) for _, cps, _ in routes_prep for cp in cps)
        )
        t_weather_0 = time.perf_counter()
        weather_map = self.weather.get_series(unique_cells)
        weather_ms = (time.perf_counter() - t_weather_0) * 1000.0

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

        if any(eta > last_forecast_time for eta in all_etas):
            raise BeyondForecastHorizonError(
                f"Trip arrival time exceeds available forecast horizon "
                f"(last available: {last_forecast_time.isoformat()})",
                last_forecast_time=last_forecast_time,
            )

        return weather_map, weather_ms, unique_cells, last_forecast_time

    def _assess_routes(
        self,
        routes_prep: list[tuple[SelectedRoute, list[Checkpoint], list[datetime.datetime]]],
        weather_map: dict[GridCell, WeatherSeries],
        load_weight_lb: float,
        last_forecast_time: datetime.datetime,
    ) -> list[tuple[SelectedRoute, tuple[AssessedCheckpoint, ...], RouteSummary]]:
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
                    load_weight_lb=load_weight_lb,
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

        return analyzed_data

    def _rank_routes(
        self,
        analyzed_data: list[tuple[SelectedRoute, tuple[AssessedCheckpoint, ...], RouteSummary]],
    ) -> Recommendation:
        ranking_inputs = [
            RankingInput(route_id=sr.route_id, label=sr.label, summary=summary)
            for sr, _, summary in analyzed_data
        ]
        return ranking.rank_routes(ranking_inputs)

    def _compile_warnings(
        self,
        route_warnings: tuple[Warning, ...],
        analyzed_data: list[tuple[SelectedRoute, tuple[AssessedCheckpoint, ...], RouteSummary]],
        no_safe_route: bool,
    ) -> tuple[Warning, ...]:
        warnings_list: list[Warning] = list(route_warnings)
        total_unavailable = sum(summary.unavailable_checkpoints for _, _, summary in analyzed_data)
        if total_unavailable > 0:
            warnings_list.append(
                Warning(
                    code="WEATHER_UNAVAILABLE_SOME",
                    message=f"{total_unavailable} checkpoint(s) have unavailable weather data.",
                )
            )
        for sr, _, summary in analyzed_data:
            if summary.distance_miles > 0:
                frac = summary.unavailable_miles / summary.distance_miles
                if frac > rules_config.INCOMPLETE_WEATHER_MAX_FRACTION:
                    pct = round(frac * 100)
                    warnings_list.append(
                        Warning(
                            code="INCOMPLETE_WEATHER",
                            message=f"{sr.label} has incomplete weather data ({pct}% unavailable).",
                        )
                    )
        if no_safe_route:
            warnings_list.append(
                Warning(
                    code="NO_SAFE_ROUTE",
                    message="No safe route available under current weather conditions.",
                )
            )
        return tuple(warnings_list)

    def _assemble_analyzed_routes(
        self,
        analyzed_data: list[tuple[SelectedRoute, tuple[AssessedCheckpoint, ...], RouteSummary]],
        recommendation: Recommendation,
    ) -> tuple[AnalyzedRoute, ...]:
        ranked_lookup = {r.route_id: r for r in recommendation.ranked}
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
        return tuple(analyzed_routes)
