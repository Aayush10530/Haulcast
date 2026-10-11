"""Pure domain corridor grid generation for corridor weather heatmaps."""

import bisect
import math
from collections.abc import Sequence

from core.domain import rules_config
from core.domain.geometry import cumulative_miles, point_at_mile
from core.domain.grid import snap_to_cell
from core.domain.route_diversity import bearing_degrees, offset_point
from core.domain.types import Coordinate, GridCell


def _local_bearing(
    polyline: Sequence[Coordinate],
    cumulative: Sequence[float],
    m: float,
) -> float:
    """Determine the forward polyline bearing at cumulative mile m."""
    if len(polyline) < 2:
        return 0.0
    idx = bisect.bisect_right(cumulative, m)
    if idx == 0:
        idx = 1
    elif idx >= len(polyline):
        idx = len(polyline) - 1

    p1 = polyline[idx - 1]
    p2 = polyline[idx]
    if p1 != p2:
        return bearing_degrees(p1, p2)

    for i in range(len(polyline) - 1):
        if polyline[i] != polyline[i + 1]:
            return bearing_degrees(polyline[i], polyline[i + 1])
    return 0.0


def generate_corridor_cells(
    routes: Sequence[tuple[Coordinate, ...]],
    route_miles: Sequence[float],
) -> list[GridCell]:
    """Generate unique snapped grid cells covering route corridors.

    Along each route, stations are sampled at spacing = max(CORRIDOR_MIN_SPACING_MILES,
    route_miles / CORRIDOR_STATIONS_PER_ROUTE). At each station, the center point and
    two lateral points at +/- CORRIDOR_HALF_WIDTH_MILES perpendicular to the local bearing
    are snapped to the weather grid and deduplicated preserving first-seen order.

    If the deduplicated cell count exceeds CORRIDOR_MAX_CELLS, spacing is increased by 25%
    and generation retried (at most 10 times, then raises ValueError).
    """
    if len(routes) != len(route_miles):
        raise ValueError(
            f"routes ({len(routes)}) and route_miles ({len(route_miles)}) length mismatch"
        )

    for dist in route_miles:
        if not math.isfinite(dist) or dist < 0.0:
            raise ValueError(f"route_miles must be non-negative finite numbers, got {dist}")

    if not routes:
        return []

    spacing_factor = 1.0
    for attempt in range(11):
        cells: list[GridCell] = []
        seen: set[GridCell] = set()

        for polyline, total_m in zip(routes, route_miles, strict=True):
            if not polyline:
                continue

            base_spacing = max(
                rules_config.CORRIDOR_MIN_SPACING_MILES,
                total_m / rules_config.CORRIDOR_STATIONS_PER_ROUTE,
            )
            spacing = base_spacing * spacing_factor

            station_points: list[tuple[Coordinate, float]] = []
            if len(polyline) < 2 or total_m <= 0.0:
                station_points.append((polyline[0], 0.0))
            else:
                cum = cumulative_miles(polyline, total_m)
                m = 0.0
                while m <= total_m or math.isclose(m, total_m, abs_tol=1e-5):
                    clamped_m = min(m, total_m)
                    pt = point_at_mile(polyline, cum, clamped_m)
                    bearing = _local_bearing(polyline, cum, clamped_m)
                    station_points.append((pt, bearing))
                    m += spacing

            for pt, bearing in station_points:
                left = offset_point(
                    pt,
                    bearing - 90.0,
                    rules_config.CORRIDOR_HALF_WIDTH_MILES,
                )
                right = offset_point(
                    pt,
                    bearing + 90.0,
                    rules_config.CORRIDOR_HALF_WIDTH_MILES,
                )
                for candidate in (pt, left, right):
                    cell = snap_to_cell(candidate)
                    if cell not in seen:
                        seen.add(cell)
                        cells.append(cell)

        if len(cells) <= rules_config.CORRIDOR_MAX_CELLS:
            return cells

        if attempt == 10:
            raise ValueError(
                f"Corridor cell count ({len(cells)}) exceeds maximum "
                f"({rules_config.CORRIDOR_MAX_CELLS}) after 10 retries."
            )

        spacing_factor *= 1.25
