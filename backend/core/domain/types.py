import datetime
import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum


class RiskLevel(IntEnum):
    """Ordinal risk level from Low (0) to No Travel (4)."""

    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4

    @property
    def key(self) -> str:
        """Lowercase API string key (e.g. 'no_travel')."""
        return self.name.lower()

    @property
    def label(self) -> str:
        """Human-readable display label (e.g. 'No Travel')."""
        return RISK_LEVEL_LABELS[self]


RISK_LEVEL_LABELS: dict[RiskLevel, str] = {
    RiskLevel.LOW: "Low",
    RiskLevel.MODERATE: "Moderate",
    RiskLevel.HIGH: "High",
    RiskLevel.SEVERE: "Severe",
    RiskLevel.NO_TRAVEL: "No Travel",
}


class RiskDriver(StrEnum):
    """Condition or rule that drives the risk level."""

    WIND = "wind"
    RAIN = "rain"
    SNOW = "snow"
    LOAD_RULE = "load_rule"


class IntervalMode(StrEnum):
    """Checkpoint interval selection mode."""

    AUTO = "auto"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class Coordinate:
    """Geographic coordinate (latitude [-90, 90], longitude [-180, 180])."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.lat) or not (-90.0 <= self.lat <= 90.0):
            raise ValueError(f"Latitude must be a finite number between -90 and 90, got {self.lat}")
        if not math.isfinite(self.lon) or not (-180.0 <= self.lon <= 180.0):
            raise ValueError(
                f"Longitude must be a finite number between -180 and 180, got {self.lon}"
            )


@dataclass(frozen=True, slots=True)
class ConditionLevels:
    """Individual risk levels evaluated for each weather condition."""

    wind: RiskLevel
    rain: RiskLevel
    snow: RiskLevel


@dataclass(frozen=True, slots=True)
class WeatherSample:
    """Weather measurements at a checkpoint, pre-rounded per A-03."""

    wind_mph: float
    rain_in_hr: float
    snow_in_hr: float


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """Risk evaluation result for a weather sample and load weight."""

    level: RiskLevel
    table_level: RiskLevel
    driver: RiskDriver
    load_rule_applied: bool
    per_condition_levels: ConditionLevels


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """Sampled checkpoint along a route corridor."""

    index: int
    mile: float
    coordinate: Coordinate
    covers_from_mile: float
    covers_to_mile: float


@dataclass(frozen=True, slots=True)
class Timeline:
    """Cumulative route timeline holding parallel distance and elapsed duration points."""

    distances_miles: tuple[float, ...]
    elapsed_seconds: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.distances_miles) != len(self.elapsed_seconds):
            raise ValueError(
                f"Distances and elapsed durations must have matching lengths: "
                f"{len(self.distances_miles)} != {len(self.elapsed_seconds)}"
            )
        if len(self.distances_miles) < 2:
            raise ValueError(
                f"Timeline must contain at least 2 points, got {len(self.distances_miles)}"
            )
        if self.distances_miles[0] != 0.0 or self.elapsed_seconds[0] != 0.0:
            raise ValueError(
                f"First point of timeline must be (0.0, 0.0), got "
                f"({self.distances_miles[0]}, {self.elapsed_seconds[0]})"
            )

        for i in range(len(self.distances_miles)):
            d = self.distances_miles[i]
            s = self.elapsed_seconds[i]
            if not math.isfinite(d) or d < 0.0:
                raise ValueError(
                    f"Distance at index {i} must be a non-negative finite number, got {d}"
                )
            if not math.isfinite(s) or s < 0.0:
                raise ValueError(
                    f"Elapsed seconds at index {i} must be a non-negative finite number, got {s}"
                )
            if d == 0.0 and s != 0.0:
                raise ValueError(
                    f"Point at distance 0 must have elapsed 0, got ({d}, {s}) at index {i}"
                )
            if i > 0:
                if d < self.distances_miles[i - 1]:
                    raise ValueError(
                        f"Distances must be non-decreasing: "
                        f"{d} < {self.distances_miles[i - 1]} at index {i}"
                    )
                if s < self.elapsed_seconds[i - 1]:
                    raise ValueError(
                        f"Elapsed seconds must be non-decreasing: "
                        f"{s} < {self.elapsed_seconds[i - 1]} at index {i}"
                    )

    @property
    def total_miles(self) -> float:
        return self.distances_miles[-1]

    @property
    def total_seconds(self) -> float:
        return self.elapsed_seconds[-1]

    @classmethod
    def from_points(cls, pairs: Sequence[tuple[float, float]]) -> "Timeline":
        """Construct Timeline from a sequence of (distance_miles, elapsed_seconds) pairs."""
        return cls(
            distances_miles=tuple(float(p[0]) for p in pairs),
            elapsed_seconds=tuple(float(p[1]) for p in pairs),
        )


@dataclass(frozen=True, slots=True)
class HourlySeries:
    """Hourly time series of weather values with fixed 3600-second step."""

    start_epoch: int
    values: tuple[float | None, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.values, tuple):
            object.__setattr__(self, "values", tuple(self.values))
        if not self.values:
            raise ValueError("HourlySeries values cannot be empty")


@dataclass(frozen=True, slots=True)
class WeatherSeries:
    """Weather series containing wind, rain, and snow hourly components."""

    tz_name: str
    wind_mph: HourlySeries
    rain_in_hr: HourlySeries
    snow_in_hr: HourlySeries

    def __post_init__(self) -> None:
        if not (
            self.wind_mph.start_epoch == self.rain_in_hr.start_epoch == self.snow_in_hr.start_epoch
        ):
            raise ValueError(
                f"HourlySeries components must have matching start_epoch: "
                f"wind={self.wind_mph.start_epoch}, rain={self.rain_in_hr.start_epoch}, "
                f"snow={self.snow_in_hr.start_epoch}"
            )
        if not (
            len(self.wind_mph.values) == len(self.rain_in_hr.values) == len(self.snow_in_hr.values)
        ):
            raise ValueError(
                f"HourlySeries components must have matching lengths: "
                f"wind={len(self.wind_mph.values)}, rain={len(self.rain_in_hr.values)}, "
                f"snow={len(self.snow_in_hr.values)}"
            )


@dataclass(frozen=True, slots=True)
class AssessedCheckpoint:
    """Checkpoint evaluated with weather measurements and risk classification."""

    checkpoint: Checkpoint
    eta_utc: datetime.datetime
    tz_name: str
    sample: WeatherSample | None
    assessment: RiskAssessment | None
    reason: str | None

    def __post_init__(self) -> None:
        if self.eta_utc.tzinfo is None or self.eta_utc.tzinfo.utcoffset(self.eta_utc) is None:
            raise ValueError(f"eta_utc must be a timezone-aware datetime, got {self.eta_utc}")
        if (self.sample is None) != (self.assessment is None):
            raise ValueError("sample and assessment must both be None or both be provided")
        if (self.reason is None) != (self.assessment is None):
            raise ValueError("reason must be provided if and only if assessment is provided")


@dataclass(frozen=True, slots=True)
class MilesByLevel:
    """Miles covered per risk level along a route corridor."""

    low: float
    moderate: float
    high: float
    severe: float
    no_travel: float

    def __post_init__(self) -> None:
        for name, val in (
            ("low", self.low),
            ("moderate", self.moderate),
            ("high", self.high),
            ("severe", self.severe),
            ("no_travel", self.no_travel),
        ):
            if not math.isfinite(val) or val < 0.0:
                raise ValueError(f"{name} miles must be a non-negative finite number, got {val}")

    def for_level(self, level: RiskLevel) -> float:
        """Return the miles covered for a specific RiskLevel."""
        match level:
            case RiskLevel.LOW:
                return self.low
            case RiskLevel.MODERATE:
                return self.moderate
            case RiskLevel.HIGH:
                return self.high
            case RiskLevel.SEVERE:
                return self.severe
            case RiskLevel.NO_TRAVEL:
                return self.no_travel


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
        if not math.isfinite(self.distance_miles) or self.distance_miles <= 0.0:
            raise ValueError(
                f"distance_miles must be a positive finite number, got {self.distance_miles}"
            )
        if not math.isfinite(self.duration_seconds) or self.duration_seconds < 0.0:
            raise ValueError(
                f"duration_seconds must be non-negative finite, got {self.duration_seconds}"
            )
        if not math.isfinite(self.unavailable_miles) or self.unavailable_miles < 0.0:
            raise ValueError(
                f"unavailable_miles must be non-negative finite, got {self.unavailable_miles}"
            )
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


class DecidingFactor(StrEnum):
    """Criterion that determined the recommended route."""

    ONLY_OPTION = "only_option"
    NO_DATA = "no_data"
    NO_TRAVEL = "no_travel"
    SEVERE_MILES = "severe_miles"
    HIGH_MILES = "high_miles"
    AVG_RISK = "avg_risk"
    TRAVEL_TIME = "travel_time"
    TIE = "tie"


@dataclass(frozen=True, slots=True)
class RankingInput:
    """Candidate route and its summary to be evaluated for ranking."""

    route_id: str
    label: str
    summary: RouteSummary

    def __post_init__(self) -> None:
        if not self.route_id or not self.route_id.strip():
            raise ValueError("route_id cannot be empty")
        if not self.label or not self.label.strip():
            raise ValueError("label cannot be empty")


@dataclass(frozen=True, slots=True)
class RankedRoute:
    """Position and duration delta of an evaluated route candidate."""

    route_id: str
    rank: int
    delta_vs_fastest_seconds: float

    def __post_init__(self) -> None:
        if not self.route_id or not self.route_id.strip():
            raise ValueError("route_id cannot be empty")
        if self.rank < 1:
            raise ValueError(f"rank must be a positive 1-based integer, got {self.rank}")
        if not math.isfinite(self.delta_vs_fastest_seconds) or self.delta_vs_fastest_seconds < 0.0:
            raise ValueError(
                f"delta_vs_fastest_seconds must be a non-negative finite number, "
                f"got {self.delta_vs_fastest_seconds}"
            )


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Overall recommendation decision, narrative headline, and ranked list."""

    route_id: str
    decided_by: DecidingFactor
    headline: str
    no_safe_route: bool
    ranked: tuple[RankedRoute, ...]

    def __post_init__(self) -> None:
        if not self.route_id or not self.route_id.strip():
            raise ValueError("route_id cannot be empty")
        if not self.headline or not self.headline.strip():
            raise ValueError("headline cannot be empty")
        if not isinstance(self.ranked, tuple):
            object.__setattr__(self, "ranked", tuple(self.ranked))
        if not self.ranked:
            raise ValueError("ranked cannot be empty")


@dataclass(frozen=True, slots=True)
class Place:
    """Geocoded place with label and coordinate."""

    label: str
    coordinate: Coordinate
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise ValueError("label cannot be empty")


@dataclass(frozen=True, slots=True)
class GridCell:
    """Weather grid cell index at discrete resolution (e.g. 0.1 degree)."""

    lat_index: int
    lon_index: int

    def __post_init__(self) -> None:
        if not isinstance(self.lat_index, int) or isinstance(self.lat_index, bool):
            raise TypeError(f"lat_index must be an int, got {type(self.lat_index)}")
        if not isinstance(self.lon_index, int) or isinstance(self.lon_index, bool):
            raise TypeError(f"lon_index must be an int, got {type(self.lon_index)}")


@dataclass(frozen=True, slots=True)
class RawRoute:
    """Raw route candidate returned by a routing provider before analysis."""

    provider_id: str
    polyline: tuple[Coordinate, ...]
    distance_miles: float
    duration_seconds: float
    timeline: Timeline
    via_summary: str | None = None

    def __post_init__(self) -> None:
        if not self.provider_id or not self.provider_id.strip():
            raise ValueError("provider_id cannot be empty")
        if not isinstance(self.polyline, tuple):
            object.__setattr__(self, "polyline", tuple(self.polyline))
        if len(self.polyline) < 2:
            raise ValueError("polyline must contain at least 2 points")
        if not math.isfinite(self.distance_miles) or self.distance_miles <= 0.0:
            raise ValueError(
                f"distance_miles must be a positive finite number, got {self.distance_miles}"
            )
        if not math.isfinite(self.duration_seconds) or self.duration_seconds < 0.0:
            raise ValueError(
                f"duration_seconds must be non-negative finite, got {self.duration_seconds}"
            )


@dataclass(frozen=True, slots=True)
class SelectedRoute:
    """Selected route candidate labeled with identifier and display label."""

    route_id: str
    label: str
    raw: RawRoute

    def __post_init__(self) -> None:
        if not self.route_id or not self.route_id.strip():
            raise ValueError("route_id cannot be empty")
        if not self.label or not self.label.strip():
            raise ValueError("label cannot be empty")
        if not isinstance(self.raw, RawRoute):
            raise TypeError(f"raw must be a RawRoute instance, got {type(self.raw)}")


@dataclass(frozen=True, slots=True)
class Warning:
    """Warning item associated with a trip or route selection."""

    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ValueError("code cannot be empty")
        if not self.message or not self.message.strip():
            raise ValueError("message cannot be empty")


@dataclass(frozen=True, slots=True)
class RouteSelection:
    """Result of route diversity and selection."""

    routes: tuple[SelectedRoute, ...]
    warnings: tuple[Warning, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.routes, tuple):
            object.__setattr__(self, "routes", tuple(self.routes))
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))


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
        if not isinstance(self.load_weight_lb, int) or isinstance(self.load_weight_lb, bool):
            raise TypeError(f"load_weight_lb must be an int, got {type(self.load_weight_lb)}")
        if self.load_weight_lb <= 0:
            raise ValueError(f"load_weight_lb must be positive, got {self.load_weight_lb}")
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
        if not self.origin_tz or not self.origin_tz.strip():
            raise ValueError("origin_tz cannot be empty")
        if self.load_weight_lb <= 0:
            raise ValueError(f"load_weight_lb must be positive, got {self.load_weight_lb}")
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
        if not self.route_id or not self.route_id.strip():
            raise ValueError("route_id cannot be empty")
        if not self.label or not self.label.strip():
            raise ValueError("label cannot be empty")
        if not isinstance(self.raw, RawRoute):
            raise TypeError(f"raw must be a RawRoute instance, got {type(self.raw)}")
        if not isinstance(self.checkpoints, tuple):
            object.__setattr__(self, "checkpoints", tuple(self.checkpoints))
        if not isinstance(self.summary, RouteSummary):
            raise TypeError(f"summary must be a RouteSummary instance, got {type(self.summary)}")
        if self.rank < 1:
            raise ValueError(f"rank must be at least 1, got {self.rank}")
        if not math.isfinite(self.delta_vs_fastest_seconds) or self.delta_vs_fastest_seconds < 0.0:
            raise ValueError(
                "delta_vs_fastest_seconds must be non-negative, "
                f"got {self.delta_vs_fastest_seconds}"
            )
        if not isinstance(self.display_polyline, tuple):
            object.__setattr__(self, "display_polyline", tuple(self.display_polyline))
        if len(self.display_polyline) < 2:
            raise ValueError("display_polyline must have at least 2 points")


@dataclass(frozen=True, slots=True)
class TripAnalysisMeta:
    """Execution metadata and performance counters for a trip analysis."""

    weather_cells: int
    route_count: int
    elapsed_ms: float

    def __post_init__(self) -> None:
        if self.weather_cells < 0:
            raise ValueError(f"weather_cells must be non-negative, got {self.weather_cells}")
        if self.route_count < 0:
            raise ValueError(f"route_count must be non-negative, got {self.route_count}")
        if not math.isfinite(self.elapsed_ms) or self.elapsed_ms < 0.0:
            raise ValueError(f"elapsed_ms must be non-negative finite, got {self.elapsed_ms}")


@dataclass(frozen=True, slots=True)
class TripAnalysis:
    """Complete trip analysis result containing routes, recommendation, and metadata."""

    request: TripRequestEcho
    routes: tuple[AnalyzedRoute, ...]
    recommendation: Recommendation
    warnings: tuple[Warning, ...]
    meta: TripAnalysisMeta

    def __post_init__(self) -> None:
        if not isinstance(self.routes, tuple):
            object.__setattr__(self, "routes", tuple(self.routes))
        if not isinstance(self.warnings, tuple):
            object.__setattr__(self, "warnings", tuple(self.warnings))


RouteRecommendation = Recommendation
