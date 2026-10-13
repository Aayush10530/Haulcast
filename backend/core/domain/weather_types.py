"""Weather-related domain types and assessed checkpoints."""

import datetime
from dataclasses import dataclass

from core.domain._validation import coerce_tuple
from core.domain.risk_types import RiskAssessment
from core.domain.route_types import Checkpoint


@dataclass(frozen=True, slots=True)
class WeatherSample:
    """Weather measurements at a checkpoint, pre-rounded per A-03."""

    wind_mph: float
    rain_in_hr: float
    snow_in_hr: float


@dataclass(frozen=True, slots=True)
class HourlySeries:
    """Hourly time series of weather values with fixed 3600-second step."""

    start_epoch: int
    values: tuple[float | None, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", coerce_tuple(self.values))
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
