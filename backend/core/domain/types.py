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
