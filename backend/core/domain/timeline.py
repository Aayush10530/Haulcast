import bisect
import datetime
import math
from collections.abc import Sequence

from core.domain.types import Checkpoint, Timeline


def constant_speed_timeline(total_miles: float, total_seconds: float) -> Timeline:
    """Create a 2-point fallback Timeline representing constant average speed."""
    if not math.isfinite(total_miles) or total_miles <= 0.0:
        raise ValueError(f"total_miles must be a positive finite number, got {total_miles}")
    if not math.isfinite(total_seconds) or total_seconds < 0.0:
        raise ValueError(f"total_seconds must be a non-negative finite number, got {total_seconds}")

    return Timeline.from_points([(0.0, 0.0), (total_miles, total_seconds)])


def elapsed_at(timeline: Timeline, mile: float) -> float:
    """Calculate elapsed driving seconds at a given cumulative route mile.

    Uses bisect and linear interpolation between timeline control points.
    Clamps miles below 0 to 0.0 and above total route distance to total_seconds.
    When multiple points share the same distance, returns the later elapsed time.
    """
    if not math.isfinite(mile):
        raise ValueError(f"mile must be a finite number, got {mile}")

    if mile <= 0.0:
        return 0.0
    if mile >= timeline.total_miles:
        return timeline.total_seconds

    i = bisect.bisect_right(timeline.distances_miles, mile)

    m0 = timeline.distances_miles[i - 1]
    s0 = timeline.elapsed_seconds[i - 1]

    # If exact match at distance marker, return the later elapsed time
    if math.isclose(mile, m0, abs_tol=1e-9):
        return s0

    m1 = timeline.distances_miles[i]
    s1 = timeline.elapsed_seconds[i]
    delta_m = m1 - m0

    t = (mile - m0) / delta_m
    return s0 + t * (s1 - s0)


def eta_at(departure: datetime.datetime, timeline: Timeline, mile: float) -> datetime.datetime:
    """Calculate the estimated time of arrival at a given route mile in UTC.

    Requires a timezone-aware departure datetime; converts to UTC if in another timezone.
    """
    if departure.tzinfo is None or departure.tzinfo.utcoffset(departure) is None:
        raise ValueError(f"departure must be a timezone-aware datetime, got {departure}")

    departure_utc = departure.astimezone(datetime.UTC)
    seconds = elapsed_at(timeline, mile)
    return departure_utc + datetime.timedelta(seconds=seconds)


def etas_for_checkpoints(
    departure: datetime.datetime,
    timeline: Timeline,
    checkpoints: Sequence[Checkpoint],
) -> list[datetime.datetime]:
    """Calculate arrival ETAs (UTC) parallel to the given sequence of checkpoints."""
    return [eta_at(departure, timeline, cp.mile) for cp in checkpoints]
