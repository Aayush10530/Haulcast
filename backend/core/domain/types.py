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
        _LABELS = {
            RiskLevel.LOW: "Low",
            RiskLevel.MODERATE: "Moderate",
            RiskLevel.HIGH: "High",
            RiskLevel.SEVERE: "Severe",
            RiskLevel.NO_TRAVEL: "No Travel",
        }
        return _LABELS[self]


class RiskDriver(StrEnum):
    """Condition or rule that drives the risk level."""

    WIND = "wind"
    RAIN = "rain"
    SNOW = "snow"
    LOAD_RULE = "load_rule"


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
