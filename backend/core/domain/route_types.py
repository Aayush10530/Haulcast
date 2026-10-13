"""Route, coordinate, timeline, and place domain types."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from core.domain._validation import (
    coerce_tuple,
    validate_non_empty_str,
    validate_non_negative_finite,
    validate_positive_finite,
)


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


def validate_coordinates(
    coords: Sequence[Coordinate], name: str = "polyline", min_count: int = 2
) -> tuple[Coordinate, ...]:
    res = coerce_tuple(coords)
    if len(res) < min_count:
        if name == "polyline":
            raise ValueError(f"{name} must contain at least {min_count} points")
        raise ValueError(f"{name} must have at least {min_count} points")
    return res


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
class Place:
    """Geocoded place with label and coordinate."""

    label: str
    coordinate: Coordinate
    id: str | None = None

    def __post_init__(self) -> None:
        validate_non_empty_str(self.label, "label")


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
        validate_non_empty_str(self.provider_id, "provider_id")
        object.__setattr__(self, "polyline", validate_coordinates(self.polyline, "polyline", 2))
        validate_positive_finite(self.distance_miles, "distance_miles")
        validate_non_negative_finite(self.duration_seconds, "duration_seconds")


@dataclass(frozen=True, slots=True)
class SelectedRoute:
    """Selected route candidate labeled with identifier and display label."""

    route_id: str
    label: str
    raw: RawRoute

    def __post_init__(self) -> None:
        validate_non_empty_str(self.route_id, "route_id")
        validate_non_empty_str(self.label, "label")
        if not isinstance(self.raw, RawRoute):
            raise TypeError(f"raw must be a RawRoute instance, got {type(self.raw)}")


@dataclass(frozen=True, slots=True)
class Warning:
    """Warning item associated with a trip or route selection."""

    code: str
    message: str

    def __post_init__(self) -> None:
        validate_non_empty_str(self.code, "code")
        validate_non_empty_str(self.message, "message")


@dataclass(frozen=True, slots=True)
class RouteSelection:
    """Result of route diversity and selection."""

    routes: tuple[SelectedRoute, ...]
    warnings: tuple[Warning, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "routes", coerce_tuple(self.routes))
        object.__setattr__(self, "warnings", coerce_tuple(self.warnings))
