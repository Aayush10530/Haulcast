"""Risk-related domain enumerations and dataclasses."""

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from core.domain._validation import validate_non_negative_finite


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


class DecidingFactor(StrEnum):
    """Criterion that determined the recommended route."""

    ONLY_OPTION = "only_option"
    INCOMPLETE_DATA = "incomplete_data"
    NO_DATA = "no_data"
    NO_TRAVEL = "no_travel"
    SEVERE_MILES = "severe_miles"
    HIGH_MILES = "high_miles"
    AVG_RISK = "avg_risk"
    TRAVEL_TIME = "travel_time"
    TIE = "tie"


@dataclass(frozen=True, slots=True)
class ConditionLevels:
    """Individual risk levels evaluated for each weather condition."""

    wind: RiskLevel
    rain: RiskLevel
    snow: RiskLevel


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """Risk evaluation result for a weather sample and load weight."""

    level: RiskLevel
    table_level: RiskLevel
    driver: RiskDriver
    load_rule_applied: bool
    per_condition_levels: ConditionLevels


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
            validate_non_negative_finite(val, f"{name} miles")

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
