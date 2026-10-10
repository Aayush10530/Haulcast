"""Live script testing TomTom routing adapter for Dallas to Denver (F-021)."""

from pathlib import Path
import os
import sys
import time

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load .env if present
env_path = backend_dir / ".env"
if env_path.exists():
    try:
        import dotenv

        dotenv.load_dotenv(env_path)
    except ImportError:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

from core.domain.types import Coordinate
from core.providers.routing_tomtom import TomTomRoutingProvider


def main() -> None:
    api_key = (os.environ.get("TOMTOM_API_KEY") or "").strip()
    if not api_key:
        print("ERROR: TOMTOM_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    origin = Coordinate(lat=32.7767, lon=-96.7970)  # Dallas, TX
    destination = Coordinate(lat=39.7392, lon=-104.9903)  # Denver, CO

    provider = TomTomRoutingProvider(api_key=api_key, timeout_seconds=15.0)

    # 1. max_routes = 2
    t0 = time.perf_counter()
    routes_2 = provider.get_routes(origin, destination, max_routes=2)
    time_2 = time.perf_counter() - t0

    # 2. max_routes = 3
    t0 = time.perf_counter()
    routes_3 = provider.get_routes(origin, destination, max_routes=3)
    time_3 = time.perf_counter() - t0

    print("=== LIVE ROUTING RESULTS (Dallas -> Denver) ===")
    print(f"max_routes=2: returned {len(routes_2)} routes in {time_2:.2f}s")
    for idx, r in enumerate(routes_2):
        hours = r.duration_seconds / 3600.0
        print(f"  Route {idx + 1}: {r.distance_miles:.1f} mi, {hours:.2f} hrs, {len(r.polyline)} polyline points")

    print(f"\nmax_routes=3: returned {len(routes_3)} routes in {time_3:.2f}s")
    for idx, r in enumerate(routes_3):
        hours = r.duration_seconds / 3600.0
        print(f"  Route {idx + 1}: {r.distance_miles:.1f} mi, {hours:.2f} hrs, {len(r.polyline)} polyline points")

    # Comparison with spike:
    # In P0 spike investigation with traffic=false & vehicleMaxSpeed=105 km/h:
    # Route 1: ~798.5 mi, ~12.91 hrs (46,476s)
    # Route 2: ~882.3 mi, ~13.74 hrs (49,464s)
    # (Without vehicleMaxSpeed/traffic=false, truck baseline was ~787.5 mi, ~12.87 hrs)
    spike_match = False
    if len(routes_3) >= 2:
        r1_dist_match = abs(routes_3[0].distance_miles - 798.5) < 5.0 or abs(routes_3[0].distance_miles - 787.5) < 15.0
        r1_dur_match = abs((routes_3[0].duration_seconds / 3600.0) - 12.91) < 0.5
        spike_match = r1_dist_match and r1_dur_match

    print(f"\nDistances/durations match spike: {'YES' if spike_match else 'NO'}")


if __name__ == "__main__":
    main()
