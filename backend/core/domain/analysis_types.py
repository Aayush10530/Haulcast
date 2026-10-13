"""Analysis, request, summary, ranking, and trip result domain types."""

import datetime
import math
from dataclasses import dataclass

from core.domain._validation import (
    coerce_tuple,
    validate_load_weight_lb,
    validate_non_empty_str,
    validate_non_negative_finite,
    validate_positive_finite,
)
from core.domain.risk_types import DecidingFactor, MilesByLevel, RiskLevel
from core.domain.route_types import (
    Coordinate,
    IntervalMode,
    Place,
    RawRoute,
    Warning,
    validate_coordinates,
)
from core.domain.weather_types import AssessedCheckpoint


@dataclass(frozen=True, slots=True)
class RouteSummary:
    """Aggregated risk and distance summary for an analyzed route corridor."""

    distance_miles: float
    duration_seconds: float
    miles_by_level: MilesByLevel
    unavailable_miles: float
    avg_risk_score: float | None
    max_level: RiskLevel | None
    unavailable_checkpoints: int

    def __post_init__(self) -> None:
        validate_positive_finite(self.distance_miles, "distance_miles")
        validate_non_negative_finite(self.duration_seconds, "duration_seconds")
        validate_non_negative_finite(self.unavailable_miles, "unavailable_miles")
        if self.avg_risk_score is not None and (
            not math.isfinite(self.avg_risk_score) or not (0.0 <= self.avg_risk_score <= 4.0)
        ):
            raise ValueError(
                f"avg_risk_score must be between 0.0 and 4.0 or None, got {self.avg_risk_score}"
            )
        if self.unavailable_checkpoints < 0:
            raise ValueError(
                f"unavailable_checkpoints must be non-negative, got {self.unavailable_checkpoints}"
            )

    @property
    def has_no_travel(self) -> bool:
        """True when max_level is NO_TRAVEL, independent of how small the covered miles are."""
        return self.max_level == RiskLevel.NO_TRAVEL


@dataclass(frozen=True, slots=True)
class RankingInput:
    """Candidate route and its summary to be evaluated for ranking."""

    route_id: str
    label: str
    summary: RouteSummary

    def __post_init__(self) -> None:
        validate_non_empty_str(self.route_id, "route_id")
        validate_non_empty_str(self.label, "label")


@dataclass(frozen=True, slots=True)
class RankedRoute:
    """Position and duration delta of an evaluated route candidate."""

    route_id: str
    rank: int
    delta_vs_fastest_seconds: float

    def __post_init__(self) -> None:
        validate_non_empty_str(self.route_id, "route_id")
        if self.rank < 1:
            raise ValueError(f"rank must be a positive 1-based integer, got {self.rank}")
        validate_non_negative_finite(self.delta_vs_fastest_seconds, "delta_vs_fastest_seconds")


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Overall recommendation decision, narrative headline, and ranked list."""

    route_id: str
    decided_by: DecidingFactor
    headline: str
    no_safe_route: bool
    ranked: tuple[RankedRoute, ...]

    def __post_init__(self) -> None:
        validate_non_empty_str(self.route_id, "route_id")
        validate_non_empty_str(self.headline, "headline")
        object.__setattr__(self, "ranked", coerce_tuple(self.ranked))
        if not self.ranked:
            raise ValueError("ranked cannot be empty")


@dataclass(frozen=True, slots=True)
class TripRequest:
    """Trip analysis input request."""

    origin: Place
    destination: Place
    departure_local: datetime.datetime
    load_weight_lb: int
    interval_mode: IntervalMode
    manual_interval: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.origin, Place):
            raise TypeError(f"origin must be a Place instance, got {type(self.origin)}")
        if not isinstance(self.destination, Place):
            raise TypeError(f"destination must be a Place instance, got {type(self.destination)}")
        if self.departure_local.tzinfo is not None:
            raise ValueError(f"departure_local must be naive datetime, got {self.departure_local}")
        validate_load_weight_lb(self.load_weight_lb)
        if not isinstance(self.interval_mode, IntervalMode):
            raise TypeError(
                f"interval_mode must be an IntervalMode, got {type(self.interval_mode)}"
            )
        if self.interval_mode == IntervalMode.MANUAL:
            if self.manual_interval is None:
                raise ValueError("manual_interval is required when interval_mode is MANUAL")


@dataclass(frozen=True, slots=True)
class TripRequestEcho:
    """Echo of validated trip request parameters in the analysis result."""

    origin: Place
    destination: Place
    departure_utc: datetime.datetime
    departure_local: datetime.datetime
    origin_tz: str
    load_weight_lb: int
    interval_miles: int
    interval_mode: IntervalMode

    def __post_init__(self) -> None:
        if (
            self.departure_utc.tzinfo is None
            or self.departure_utc.tzinfo.utcoffset(self.departure_utc) is None
        ):
            raise ValueError(f"departure_utc must be timezone-aware, got {self.departure_utc}")
        if self.departure_local.tzinfo is not None:
            raise ValueError(f"departure_local must be naive datetime, got {self.departure_local}")
        validate_non_empty_str(self.origin_tz, "origin_tz")
        validate_load_weight_lb(self.load_weight_lb)
        if self.interval_miles <= 0:
            raise ValueError(f"interval_miles must be positive, got {self.interval_miles}")


@dataclass(frozen=True, slots=True)
class AnalyzedRoute:
    """Fully analyzed route option with checkpoints, weather, risk summary, and rank."""

    route_id: str
    label: str
    raw: RawRoute
    checkpoints: tuple[AssessedCheckpoint, ...]
    summary: RouteSummary
    rank: int
    delta_vs_fastest_seconds: float
    is_recommended: bool
    display_polyline: tuple[Coordinate, ...]
    via_summary: str | None = None

    def __post_init__(self) -> None:
        validate_non_empty_str(self.route_id, "route_id")
        validate_non_empty_str(self.label, "label")
        if not isinstance(self.raw, RawRoute):
            raise TypeError(f"raw must be a RawRoute instance, got {type(self.raw)}")
        object.__setattr__(self, "checkpoints", coerce_tuple(self.checkpoints))
        if not isinstance(self.summary, RouteSummary):
            raise TypeError(f"summary must be a RouteSummary instance, got {type(self.summary)}")
        if self.rank < 1:
            raise ValueError(f"rank must be at least 1, got {self.rank}")
        validate_non_negative_finite(self.delta_vs_fastest_seconds, "delta_vs_fastest_seconds")
        object.__setattr__(
            self,
            "display_polyline",
            validate_coordinates(self.display_polyline, "display_polyline", 2),
        )


@dataclass(frozen=True, slots=True)
class TripAnalysisMeta:
    """Execution metadata and performance counters for a trip analysis."""

    weather_cells: int
    route_count: int
    elapsed_ms: float
    routing_ms: float = 0.0
    weather_ms: float = 0.0
    in_process_ms: float = 0.0

    def __post_init__(self) -> None:
        if self.weather_cells < 0:
            raise ValueError(f"weather_cells must be non-negative, got {self.weather_cells}")
        if self.route_count < 0:
            raise ValueError(f"route_count must be non-negative, got {self.route_count}")
        validate_non_negative_finite(self.elapsed_ms, "elapsed_ms")
        validate_non_negative_finite(self.routing_ms, "routing_ms")
        validate_non_negative_finite(self.weather_ms, "weather_ms")
        validate_non_negative_finite(self.in_process_ms, "in_process_ms")


@dataclass(frozen=True, slots=True)
class TripAnalysis:
    """Complete trip analysis result containing routes, recommendation, and metadata."""

    request: TripRequestEcho
    routes: tuple[AnalyzedRoute, ...]
    recommendation: Recommendation
    warnings: tuple[Warning, ...]
    meta: TripAnalysisMeta

    def __post_init__(self) -> None:
        object.__setattr__(self, "routes", coerce_tuple(self.routes))
        object.__setattr__(self, "warnings", coerce_tuple(self.warnings))


RouteRecommendation = Recommendation
