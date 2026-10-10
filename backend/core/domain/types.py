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
