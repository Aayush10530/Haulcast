import math
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
