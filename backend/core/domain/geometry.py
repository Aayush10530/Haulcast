import bisect
import math
from collections.abc import Sequence

from core.domain import rules_config
from core.domain.types import Coordinate

METERS_PER_MILE: float = 1609.344


def haversine_miles(coord1: Coordinate, coord2: Coordinate) -> float:
    """Calculate the great-circle distance between two coordinates in miles."""
    lat1_rad = math.radians(coord1.lat)
    lon1_rad = math.radians(coord1.lon)
    lat2_rad = math.radians(coord2.lat)
    lon2_rad = math.radians(coord2.lon)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return rules_config.EARTH_RADIUS_MILES * c


def cumulative_miles(polyline: Sequence[Coordinate], total_miles: float) -> list[float]:
    """Calculate cumulative distances scaled to match the provider total distance."""
    if len(polyline) < 2:
        raise ValueError(f"Polyline must contain at least 2 coordinates, got {len(polyline)}")
    if not math.isfinite(total_miles) or total_miles <= 0.0:
        raise ValueError(f"total_miles must be a positive finite number, got {total_miles}")

    unscaled = [0.0]
    for i in range(1, len(polyline)):
        dist = haversine_miles(polyline[i - 1], polyline[i])
        unscaled.append(unscaled[-1] + dist)

    unscaled_total = unscaled[-1]
    if unscaled_total == 0.0:
        raise ValueError("Unscaled geometric length of polyline is 0 while total_miles > 0")

    scale = total_miles / unscaled_total
    scaled = [min(total_miles, d * scale) for d in unscaled]
    scaled[-1] = total_miles

    return scaled


def point_at_mile(
    polyline: Sequence[Coordinate],
    cumulative: Sequence[float],
    m: float,
) -> Coordinate:
    """Interpolate a Coordinate along a polyline at a given cumulative mile.

    Uses plain linear interpolation of latitude and longitude between adjacent vertices.
    Note: Assumes contiguous routing without antimeridian crossing (-180/180 discontinuity).
    """
    if len(polyline) < 2:
        raise ValueError(f"Polyline must contain at least 2 coordinates, got {len(polyline)}")
    if len(polyline) != len(cumulative):
        raise ValueError(
            f"Polyline length ({len(polyline)}) must match cumulative length ({len(cumulative)})"
        )

    total = cumulative[-1]
    if m <= 0.0:
        return polyline[0]
    if m >= total:
        return polyline[-1]

    i = bisect.bisect_right(cumulative, m)

    m0 = cumulative[i - 1]
    m1 = cumulative[i]
    delta_m = m1 - m0
    t = (m - m0) / delta_m
    p0 = polyline[i - 1]
    p1 = polyline[i]

    interp_lat = p0.lat + t * (p1.lat - p0.lat)
    interp_lon = p0.lon + t * (p1.lon - p0.lon)
    return Coordinate(lat=interp_lat, lon=interp_lon)


def simplify(polyline: Sequence[Coordinate], tolerance_m: float) -> list[Coordinate]:
    """Simplify polyline using iterative Douglas-Peucker in a local metric projection."""
    if not math.isfinite(tolerance_m) or tolerance_m < 0.0:
        raise ValueError(f"tolerance_m must be a non-negative finite number, got {tolerance_m}")
    if len(polyline) <= 2 or tolerance_m == 0.0:
        return list(polyline)

    # Local equirectangular metric projection around polyline centroid
    mean_lat = sum(p.lat for p in polyline) / len(polyline)
    mean_lon = sum(p.lon for p in polyline) / len(polyline)
    lat0_rad = math.radians(mean_lat)
    lon0_rad = math.radians(mean_lon)
    earth_radius_m = rules_config.EARTH_RADIUS_MILES * METERS_PER_MILE
    cos_lat0 = math.cos(lat0_rad)

    points_xy: list[tuple[float, float]] = []
    for p in polyline:
        x = (math.radians(p.lon) - lon0_rad) * earth_radius_m * cos_lat0
        y = (math.radians(p.lat) - lat0_rad) * earth_radius_m
        points_xy.append((x, y))

    n = len(polyline)
    keep = [False] * n
    keep[0] = True
    keep[n - 1] = True

    stack: list[tuple[int, int]] = [(0, n - 1)]

    while stack:
        start_idx, end_idx = stack.pop()
        if end_idx <= start_idx + 1:
            continue

        x1, y1 = points_xy[start_idx]
        x2, y2 = points_xy[end_idx]
        dx = x2 - x1
        dy = y2 - y1
        seg_len_sq = dx * dx + dy * dy

        max_dist = 0.0
        max_idx = start_idx

        for i in range(start_idx + 1, end_idx):
            xp, yp = points_xy[i]
            if seg_len_sq == 0.0:
                dist = math.hypot(xp - x1, yp - y1)
            else:
                dist = abs(dy * xp - dx * yp + x2 * y1 - y2 * x1) / math.sqrt(seg_len_sq)

            if dist > max_dist:
                max_dist = dist
                max_idx = i

        if max_dist > tolerance_m:
            keep[max_idx] = True
            stack.append((start_idx, max_idx))
            stack.append((max_idx, end_idx))

    return [polyline[i] for i in range(n) if keep[i]]
