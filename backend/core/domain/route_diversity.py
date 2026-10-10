"""Route diversity analysis and candidate selection."""

import math
from collections.abc import Sequence

from core.domain import rules_config
from core.domain.geometry import haversine_miles, point_at_mile
from core.domain.types import Coordinate, RawRoute


def bearing_degrees(a: Coordinate, b: Coordinate) -> float:
    """Calculate the initial forward bearing from coordinate a to b in degrees [0, 360)."""
    if a == b:
        return 0.0
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlon = math.radians(b.lon - a.lon)

    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    initial_bearing = math.atan2(y, x)
    return (math.degrees(initial_bearing) + 360.0) % 360.0


def offset_point(origin: Coordinate, bearing_degrees: float, miles: float) -> Coordinate:
    """Calculate destination coordinate from origin along bearing for given miles."""
    if not math.isfinite(miles):
        raise ValueError(f"miles must be finite, got {miles}")
    if miles == 0.0:
        return origin

    angular_dist = miles / rules_config.EARTH_RADIUS_MILES
    bearing_rad = math.radians(bearing_degrees % 360.0)
    lat1 = math.radians(origin.lat)
    lon1 = math.radians(origin.lon)

    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_dist)
        + math.cos(lat1) * math.sin(angular_dist) * math.cos(bearing_rad)
    )
    lon2 = lon1 + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(lat1),
        math.cos(angular_dist) - math.sin(lat1) * math.sin(lat2),
    )

    lat_deg = math.degrees(lat2)
    lat_deg = max(-90.0, min(90.0, lat_deg))

    lon_deg = (math.degrees(lon2) + 180.0) % 360.0 - 180.0
    return Coordinate(lat=lat_deg, lon=lon_deg)


def densify_polyline(
    polyline: Sequence[Coordinate],
    max_step_miles: float = 0.1,
) -> list[Coordinate]:
    """Densify a polyline so adjacent vertices are spaced at most max_step_miles apart."""
    if len(polyline) < 2:
        raise ValueError(f"Polyline must contain at least 2 coordinates, got {len(polyline)}")
    if not math.isfinite(max_step_miles) or max_step_miles <= 0.0:
        raise ValueError(f"max_step_miles must be positive finite, got {max_step_miles}")

    result: list[Coordinate] = [polyline[0]]
    for i in range(1, len(polyline)):
        p0 = polyline[i - 1]
        p1 = polyline[i]
        dist = haversine_miles(p0, p1)
        if dist <= max_step_miles:
            result.append(p1)
        else:
            num_steps = max(1, math.ceil(round(dist / max_step_miles, 9)))
            for step in range(1, num_steps):
                frac = step / num_steps
                interp_lat = p0.lat + frac * (p1.lat - p0.lat)
                interp_lon = p0.lon + frac * (p1.lon - p0.lon)
                result.append(Coordinate(lat=interp_lat, lon=interp_lon))
            result.append(p1)
    return result


class _PolylineSpatialIndex:
    """Spatial grid index for fast proximity queries against a polyline."""

    def __init__(self, points: Sequence[Coordinate], cell_size_deg: float = 0.01) -> None:
        self.cell_size_deg = cell_size_deg
        self.grid: dict[tuple[int, int], list[Coordinate]] = {}
        for pt in points:
            gx = math.floor(pt.lon / cell_size_deg)
            gy = math.floor(pt.lat / cell_size_deg)
            self.grid.setdefault((gx, gy), []).append(pt)

    def is_within(self, pt: Coordinate, tolerance_miles: float) -> bool:
        """Check whether pt is within tolerance_miles of any indexed point."""
        dlat_deg = tolerance_miles / 68.7
        cos_lat = max(0.05, math.cos(math.radians(abs(pt.lat))))
        dlon_deg = tolerance_miles / (68.7 * cos_lat)

        min_gx = math.floor((pt.lon - dlon_deg) / self.cell_size_deg)
        max_gx = math.floor((pt.lon + dlon_deg) / self.cell_size_deg)
        min_gy = math.floor((pt.lat - dlat_deg) / self.cell_size_deg)
        max_gy = math.floor((pt.lat + dlat_deg) / self.cell_size_deg)

        for gy in range(min_gy, max_gy + 1):
            for gx in range(min_gx, max_gx + 1):
                bucket = self.grid.get((gx, gy))
                if bucket is not None:
                    for candidate in bucket:
                        if haversine_miles(pt, candidate) <= tolerance_miles:
                            return True
        return False


def shared_fraction(
    candidate_polyline: Sequence[Coordinate],
    other_polyline: Sequence[Coordinate],
) -> float:
    """Calculate fraction of candidate_polyline that lies within tolerance of other_polyline."""
    if len(candidate_polyline) < 2 or len(other_polyline) < 2:
        raise ValueError("Polylines must contain at least 2 coordinates")

    if tuple(candidate_polyline) == tuple(other_polyline):
        return 1.0

    # Calculate cumulative distance along candidate polyline
    cand_cum = [0.0]
    for i in range(1, len(candidate_polyline)):
        d = haversine_miles(candidate_polyline[i - 1], candidate_polyline[i])
        cand_cum.append(cand_cum[-1] + d)

    total_miles = cand_cum[-1]
    if total_miles == 0.0:
        return 1.0 if candidate_polyline[0] == other_polyline[0] else 0.0

    # Densify other polyline to at most 0.1 mile spacing and build grid hash index
    densified_other = densify_polyline(other_polyline, max_step_miles=0.1)
    index = _PolylineSpatialIndex(densified_other)

    # Sample candidate every ROUTE_OVERLAP_SAMPLE_MILES using point_at_mile
    sample_step = rules_config.ROUTE_OVERLAP_SAMPLE_MILES
    sample_miles: list[float] = []
    m = 0.0
    while m < total_miles:
        sample_miles.append(m)
        m += sample_step

    if not sample_miles or not math.isclose(sample_miles[-1], total_miles, abs_tol=1e-6):
        sample_miles.append(total_miles)

    shared_samples = 0
    for sample_m in sample_miles:
        sample_pt = point_at_mile(candidate_polyline, cand_cum, sample_m)
        if index.is_within(sample_pt, rules_config.ROUTE_OVERLAP_TOLERANCE_MILES):
            shared_samples += 1

    return shared_samples / len(sample_miles)


def select_routes(
    candidates: Sequence[RawRoute],
    max_routes: int = rules_config.MAX_ROUTES,
) -> list[RawRoute]:
    """Select up to max_routes diverse candidates sorted by duration."""
    if not candidates or max_routes <= 0:
        return []

    # Sort by duration ascending
    sorted_candidates = sorted(candidates, key=lambda r: r.duration_seconds)

    # Fastest route defines maximum allowed duration threshold
    fastest = sorted_candidates[0]
    max_duration = fastest.duration_seconds * rules_config.ROUTE_MAX_DURATION_RATIO

    # Drop candidates over ROUTE_MAX_DURATION_RATIO times the fastest
    eligible = [r for r in sorted_candidates if r.duration_seconds <= max_duration]

    kept: list[RawRoute] = [fastest]
    pool = [r for r in eligible if r is not fastest]

    while len(kept) < max_routes and pool:
        qualifying: list[tuple[RawRoute, float]] = []
        for cand in pool:
            # Check maximum shared fraction against all currently kept routes
            # Note: identical polylines have shared_fraction = 1.0 and will exceed ROUTE_OVERLAP_MAX
            max_shared = max(
                shared_fraction(cand.polyline, kept_route.polyline) for kept_route in kept
            )
            # Accept if at most ROUTE_OVERLAP_MAX (e.g. 0.85)
            if max_shared <= rules_config.ROUTE_OVERLAP_MAX or math.isclose(
                max_shared, rules_config.ROUTE_OVERLAP_MAX, abs_tol=1e-7
            ):
                qualifying.append((cand, max_shared))

        if not qualifying:
            break

        # Repeatedly add the candidate with the lowest maximum shared_fraction against kept routes
        # Tie-break by duration (first among equal lowest overlap)
        best_cand, _ = min(qualifying, key=lambda item: (item[1], item[0].duration_seconds))
        kept.append(best_cand)
        pool = [r for r in pool if r is not best_cand]

    return kept
