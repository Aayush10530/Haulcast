"""Route selection service orchestrating provider calls, via fallback, and caching."""

import bisect
import logging
from concurrent.futures import Executor, ThreadPoolExecutor

from core.domain import rules_config
from core.domain.geometry import cumulative_miles, point_at_mile
from core.domain.route_diversity import bearing_degrees, offset_point, select_routes
from core.domain.types import Coordinate, RawRoute, RouteSelection, SelectedRoute, Warning
from core.providers.base import Cache, RoutingProvider

logger = logging.getLogger(__name__)

ROUTE_IDS: tuple[str, ...] = ("route_a", "route_b", "route_c")
ROUTE_LABELS: tuple[str, ...] = ("Route A", "Route B", "Route C")


class RouteSelectionService:
    """Service to fetch, select diverse routes, and execute via waypoint fallback."""

    def __init__(
        self,
        provider: RoutingProvider,
        cache: Cache,
        ttl_seconds: int,
        workers: int = 4,
        executor: Executor | None = None,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.ttl_seconds = ttl_seconds
        self.workers = workers
        self._executor = executor

    def _cache_key(self, origin: Coordinate, destination: Coordinate) -> str:
        return (
            f"route_sel:{origin.lat:.4f}:{origin.lon:.4f}:"
            f"{destination.lat:.4f}:{destination.lon:.4f}"
        )

    def _generate_via_points(self, route: RawRoute) -> list[Coordinate]:
        """Generate 4 via coordinates perpendicular to anchors at 33% and 66% along route."""
        total_miles = route.distance_miles
        polyline = route.polyline
        cum = cumulative_miles(polyline, total_miles)

        raw_offset = rules_config.VIA_OFFSET_FRACTION * total_miles
        offset_miles = max(
            rules_config.VIA_OFFSET_MIN_MILES,
            min(rules_config.VIA_OFFSET_MAX_MILES, raw_offset),
        )

        via_points: list[Coordinate] = []
        for frac in rules_config.VIA_ANCHOR_FRACTIONS:
            anchor_m = frac * total_miles
            anchor_pt = point_at_mile(polyline, cum, anchor_m)

            # Determine local segment bearing around anchor_m
            i = bisect.bisect_right(cum, anchor_m)
            p0 = polyline[max(0, i - 1)]
            p1 = polyline[min(len(polyline) - 1, i)]
            local_bearing = bearing_degrees(p0, p1)

            # Left and right perpendicular bearings
            bearing_left = (local_bearing - 90.0) % 360.0
            bearing_right = (local_bearing + 90.0) % 360.0

            via_points.append(offset_point(anchor_pt, bearing_left, offset_miles))
            via_points.append(offset_point(anchor_pt, bearing_right, offset_miles))

        return via_points

    def _fetch_via_route(
        self,
        origin: Coordinate,
        destination: Coordinate,
        via_pt: Coordinate,
    ) -> list[RawRoute]:
        """Fetch route through via point; ignore and log any failures at WARNING."""
        try:
            return self.provider.get_routes(
                origin=origin,
                destination=destination,
                via=(via_pt,),
                max_routes=1,
            )
        except Exception as exc:
            logger.warning("Via waypoint routing request failed: %s", type(exc).__name__)
            return []

    def get_routes(self, origin: Coordinate, destination: Coordinate) -> RouteSelection:
        """Get up to MAX_ROUTES diverse routes between origin and destination."""
        cache_key = self._cache_key(origin, destination)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Native provider call with max_routes=MAX_ROUTES
        # Provider errors (NoRouteFound, ProviderTimeout, etc.) propagate directly
        native_routes = self.provider.get_routes(
            origin=origin,
            destination=destination,
            max_routes=rules_config.MAX_ROUTES,
        )

        selected = select_routes(native_routes, max_routes=rules_config.MAX_ROUTES)

        # If fewer than MAX_ROUTES, execute parallel via waypoint fallback
        if len(selected) < rules_config.MAX_ROUTES and native_routes:
            fastest_native = min(native_routes, key=lambda r: r.duration_seconds)
            via_points = self._generate_via_points(fastest_native)

            via_routes: list[RawRoute] = []
            if self._executor is not None:
                futures = [
                    self._executor.submit(self._fetch_via_route, origin, destination, pt)
                    for pt in via_points
                ]
                for f in futures:
                    via_routes.extend(f.result())
            else:
                with ThreadPoolExecutor(max_workers=self.workers) as executor:
                    futures = [
                        executor.submit(self._fetch_via_route, origin, destination, pt)
                        for pt in via_points
                    ]
                    for f in futures:
                        via_routes.extend(f.result())

            # Pool native and via routes, then select diverse routes again
            pool = list(native_routes) + via_routes
            selected = select_routes(pool, max_routes=rules_config.MAX_ROUTES)

        warnings: list[Warning] = []
        if len(selected) < rules_config.MAX_ROUTES:
            warnings.append(
                Warning(
                    code="FEWER_THAN_3_ROUTES",
                    message=f"Only {len(selected)} diverse route(s) found.",
                )
            )

        # Label by ascending duration: id route_a, route_b, route_c; label "Route A", etc.
        sorted_routes = sorted(selected, key=lambda r: r.duration_seconds)
        selected_routes: list[SelectedRoute] = []
        for idx, route in enumerate(sorted_routes):
            route_id = ROUTE_IDS[idx] if idx < len(ROUTE_IDS) else f"route_{idx + 1}"
            label = ROUTE_LABELS[idx] if idx < len(ROUTE_LABELS) else f"Route {idx + 1}"
            selected_routes.append(
                SelectedRoute(
                    route_id=route_id,
                    label=label,
                    raw=route,
                )
            )

        result = RouteSelection(
            routes=tuple(selected_routes),
            warnings=tuple(warnings),
        )

        self.cache.set(cache_key, result, self.ttl_seconds)
        return result
