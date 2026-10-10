import math
from collections.abc import Sequence

from core.domain import rules_config
from core.domain.geometry import point_at_mile
from core.domain.types import Checkpoint, Coordinate, IntervalMode


def resolve_interval(
    mode: IntervalMode,
    manual_miles: int | None,
    longest_route_miles: float,
) -> int:
    """Determine checkpoint interval in miles based on mode and route distance."""
    if not isinstance(mode, IntervalMode):
        raise ValueError(f"mode must be an IntervalMode enum instance, got {mode}")
    if not math.isfinite(longest_route_miles) or longest_route_miles < 0.0:
        raise ValueError(
            f"longest_route_miles must be a finite non-negative number, got {longest_route_miles}"
        )

    if mode == IntervalMode.AUTO:
        if longest_route_miles <= rules_config.AUTO_INTERVAL_SHORT_MAX_MILES:
            return rules_config.AUTO_INTERVAL_SHORT_MILES
        if longest_route_miles <= rules_config.AUTO_INTERVAL_MEDIUM_MAX_MILES:
            return rules_config.AUTO_INTERVAL_MEDIUM_MILES
        return rules_config.AUTO_INTERVAL_LONG_MILES

    if manual_miles not in rules_config.ALLOWED_INTERVALS:
        raise ValueError(
            f"manual_miles must be one of {rules_config.ALLOWED_INTERVALS}, got {manual_miles}"
        )
    return int(manual_miles)


def checkpoint_miles(total: float, interval: int) -> list[float]:
    """Generate checkpoint cumulative mile markers along a route of length total."""
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"total distance must be a positive finite number, got {total}")
    if interval <= 0:
        raise ValueError(f"interval must be a positive integer, got {interval}")

    miles: list[float] = []
    k = 0
    while True:
        m = float(k * interval)
        if m > total or math.isclose(m, total, abs_tol=1e-9):
            break
        miles.append(m)
        k += 1

    miles.append(float(total))
    return miles


def build_checkpoints(
    polyline: Sequence[Coordinate],
    cumulative: Sequence[float],
    interval: int,
) -> list[Checkpoint]:
    """Build Checkpoint objects along a polyline using the midpoint coverage rule."""
    if len(polyline) < 2:
        raise ValueError(f"Polyline must contain at least 2 coordinates, got {len(polyline)}")
    if len(polyline) != len(cumulative):
        raise ValueError(
            f"Polyline length ({len(polyline)}) must match cumulative length ({len(cumulative)})"
        )
    for i in range(1, len(cumulative)):
        if cumulative[i] < cumulative[i - 1]:
            raise ValueError(
                f"cumulative distances must be monotonic non-decreasing, at index {i}: "
                f"{cumulative[i]} < {cumulative[i - 1]}"
            )

    total = cumulative[-1]
    miles = checkpoint_miles(total, interval)
    n = len(miles)

    checkpoints: list[Checkpoint] = []
    for i in range(n):
        m = miles[i]
        coord = point_at_mile(polyline, cumulative, m)

        if i == 0:
            covers_from = 0.0
        else:
            covers_from = (miles[i - 1] + m) / 2.0

        if i == n - 1:
            covers_to = total
        else:
            covers_to = (m + miles[i + 1]) / 2.0

        checkpoints.append(
            Checkpoint(
                index=i,
                mile=m,
                coordinate=coord,
                covers_from_mile=covers_from,
                covers_to_mile=covers_to,
            )
        )

    return checkpoints
