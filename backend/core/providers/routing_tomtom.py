"""TomTom routing provider adapter."""

import time
from collections.abc import Callable, Sequence
from typing import Any

import httpx

from core.domain import rules_config
from core.domain.types import Coordinate, RawRoute, Timeline
from core.providers.base import (
    NoRouteFound,
    ProviderBadResponse,
)
from core.providers.http import execute_request_with_retry


def _is_no_route_error(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    detailed = data.get("detailedError")
    if isinstance(detailed, dict):
        code = str(detailed.get("code", "")).upper()
        msg = str(detailed.get("message", "")).lower()
        if "NO_ROUTE" in code or "NOT_FOUND" in code or "no route" in msg:
            return True
    msg = str(data.get("message", "")).lower()
    return "no route" in msg or "not found" in msg


def _parse_polyline(legs: list[dict[str, Any]]) -> tuple[Coordinate, ...]:
    points: list[Coordinate] = []
    for leg in legs:
        leg_pts = leg.get("points", [])
        for pt_idx, pt in enumerate(leg_pts):
            try:
                coord = Coordinate(lat=float(pt["latitude"]), lon=float(pt["longitude"]))
            except (KeyError, ValueError, TypeError):
                raise ProviderBadResponse("Invalid coordinates in route leg") from None
            if points and pt_idx == 0 and coord == points[-1]:
                continue
            points.append(coord)
    if len(points) < 2:
        raise ProviderBadResponse("Route polyline contains fewer than 2 coordinates")
    return tuple(points)


def _parse_timeline(
    instructions: list[dict[str, Any]],
    distance_miles: float,
    duration_seconds: float,
) -> Timeline:
    raw_points: list[tuple[float, float]] = []
    for inst in instructions:
        if "routeOffsetInMeters" in inst and "travelTimeInSeconds" in inst:
            d = inst["routeOffsetInMeters"] / rules_config.METERS_PER_MILE
            t = float(inst["travelTimeInSeconds"])
            raw_points.append((d, t))

    if not raw_points:
        raw_points = [(0.0, 0.0), (distance_miles, duration_seconds)]
    else:
        if raw_points[0][0] == 0.0:
            raw_points[0] = (0.0, 0.0)
        elif raw_points[0] != (0.0, 0.0):
            raw_points.insert(0, (0.0, 0.0))

        last_pt = (distance_miles, duration_seconds)
        if raw_points[-1] != last_pt:
            if raw_points[-1][0] >= distance_miles or raw_points[-1][1] >= duration_seconds:
                raw_points[-1] = last_pt
            else:
                raw_points.append(last_pt)

    deduped: list[tuple[float, float]] = [raw_points[0]]
    for pt in raw_points[1:]:
        if pt != deduped[-1]:
            deduped.append(pt)

    try:
        return Timeline.from_points(deduped)
    except ValueError:
        raise ProviderBadResponse("Invalid timeline data in route instructions") from None


class TomTomRoutingProvider:
    """RoutingProvider adapter for TomTom Routing API."""

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 8.0,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key cannot be empty")
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds
        self._client = client
        self.sleep = sleep

    def _execute_request(
        self,
        client: httpx.Client,
        url: str,
        params: dict[str, Any],
    ) -> httpx.Response:
        return execute_request_with_retry(
            client=client,
            url=url,
            params=params,
            service_label="Routing",
            sleep_fn=self.sleep,
        )

    def _parse_route(self, idx: int, route_dict: dict[str, Any]) -> RawRoute:
        if not isinstance(route_dict, dict):
            raise ProviderBadResponse("Invalid route object in response")

        summary = route_dict.get("summary")
        if not isinstance(summary, dict):
            raise ProviderBadResponse("Route summary missing or invalid")

        if "lengthInMeters" not in summary or "travelTimeInSeconds" not in summary:
            raise ProviderBadResponse("Route summary missing length or duration")

        distance_miles = summary["lengthInMeters"] / rules_config.METERS_PER_MILE
        duration_seconds = float(summary["travelTimeInSeconds"])

        legs = route_dict.get("legs", [])
        if not isinstance(legs, list) or not legs:
            raise ProviderBadResponse("Route legs missing or empty")

        polyline = _parse_polyline(legs)

        instructions = route_dict.get("guidance", {}).get("instructions", [])
        if not isinstance(instructions, list):
            instructions = []

        timeline = _parse_timeline(instructions, distance_miles, duration_seconds)

        return RawRoute(
            provider_id=f"tomtom_{idx}",
            polyline=polyline,
            distance_miles=distance_miles,
            duration_seconds=duration_seconds,
            timeline=timeline,
            via_summary=None,
        )

    def get_routes(
        self,
        origin: Coordinate,
        destination: Coordinate,
        via: Sequence[Coordinate] = (),
        max_routes: int = 3,
    ) -> list[RawRoute]:
        """Fetch truck routes between origin and destination, optionally via waypoints."""
        coords = [origin, *via, destination]
        locations = ":".join(f"{c.lat},{c.lon}" for c in coords)
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{locations}/json"

        max_alternatives = (max_routes - 1) if not via and max_routes > 1 else 0
        params: dict[str, Any] = {
            "key": self.api_key,
            "travelMode": "truck",
            "traffic": "false",
            "vehicleMaxSpeed": rules_config.TRUCK_MAX_SPEED_KMH,
            "instructionsType": "tagged",
            "computeTravelTimeFor": "all",
            "maxAlternatives": max_alternatives,
        }

        if self._client is not None:
            resp = self._execute_request(self._client, url, params)
        else:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                resp = self._execute_request(client, url, params)

        if resp.status_code != 200:
            try:
                body = resp.json()
            except Exception:
                raise ProviderBadResponse("Routing provider returned malformed error") from None
            if _is_no_route_error(body):
                raise NoRouteFound("No route found between requested coordinates")
            raise ProviderBadResponse("Routing provider returned error response")

        try:
            data = resp.json()
        except Exception:
            raise ProviderBadResponse("Routing provider returned unparseable JSON") from None

        if not isinstance(data, dict):
            raise ProviderBadResponse("Routing provider response must be a JSON object")

        raw_routes = data.get("routes")
        if not raw_routes:
            raise NoRouteFound("No route found between requested coordinates")

        parsed: list[RawRoute] = []
        for idx, r in enumerate(raw_routes[:max_routes]):
            parsed.append(self._parse_route(idx, r))

        return parsed
