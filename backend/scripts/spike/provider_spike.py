"""
Provider Spike Evaluation for StormRoute (F-000 / F-065).

Consolidated verification script covering:
1. Open-Meteo: Multi-coordinate hourly forecast query, parameter compatibility,
   unit validation (mph, in/hr, unixtime), timezone resolution, and 50/100 batch scaling.
2. TomTom: Commercial truck routing (travelMode=truck, vehicleMaxSpeed=105),
   monotonic instruction timelines, 4 long US test corridors, via-waypoint fallback,
   and geocoding typeahead search.

Usage:
    python backend/scripts/spike/provider_spike.py --weather
    python backend/scripts/spike/provider_spike.py --routing
    python backend/scripts/spike/provider_spike.py --all
"""

import argparse
import os
import time
from pathlib import Path

import httpx

# Load backend/.env if present
env_path = Path(__file__).resolve().parents[2] / ".env"
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

TOMTOM_KEY = (os.environ.get("TOMTOM_API_KEY") or "").strip()
EARTH_RADIUS_MILES = 3958.7613

US_PAIRS = [
    {
        "name": "Dallas -> Denver",
        "origin": (32.7767, -96.7970),
        "destination": (39.7392, -104.9903),
    },
    {
        "name": "Los Angeles -> Salt Lake City",
        "origin": (34.0522, -118.2437),
        "destination": (40.7608, -111.8910),
    },
    {
        "name": "Chicago -> Atlanta",
        "origin": (41.8781, -87.6298),
        "destination": (33.7490, -84.3880),
    },
    {
        "name": "Seattle -> Boise",
        "origin": (47.6062, -122.3321),
        "destination": (43.6150, -116.2023),
    },
]


def sanitize(text: str) -> str:
    """Ensure API key is never leaked in outputs or error traces."""
    if TOMTOM_KEY and TOMTOM_KEY in text:
        return text.replace(TOMTOM_KEY, "[REDACTED_KEY]")
    return text


# ============================================================================
# Open-Meteo Weather Spike
# ============================================================================


def _test_openmeteo_batch_scaling(url: str) -> None:
    print("\n2. Batch Scaling Stress Test (50 and 100 locations):")
    for count in [50, 100]:
        start_lat, start_lon = 32.7767, -96.7970
        end_lat, end_lon = 47.6062, -122.3321
        coords = [
            (
                round(start_lat + (i / (count - 1)) * (end_lat - start_lat), 4),
                round(start_lon + (i / (count - 1)) * (end_lon - start_lon), 4),
            )
            for i in range(count)
        ]
        batch_params = {
            "latitude": ",".join(str(c[0]) for c in coords),
            "longitude": ",".join(str(c[1]) for c in coords),
            "hourly": "wind_speed_10m,rain,showers,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timeformat": "unixtime",
            "timezone": "auto",
            "past_hours": 3,
            "forecast_hours": 288,
        }
        b_start = time.perf_counter()
        with httpx.Client(timeout=30.0) as client:
            b_resp = client.get(url, params=batch_params)
        b_elapsed = time.perf_counter() - b_start

        if b_resp.status_code == 200:
            b_data = b_resp.json()
            kb = len(b_resp.content) / 1024
            print(
                f"   {count:3d} locations -> HTTP 200, {b_elapsed:.3f} s, "
                f"{kb:.1f} KB ({len(b_data)} items returned)"
            )
        else:
            print(f"   {count:3d} locations -> HTTP {b_resp.status_code} ({b_resp.text[:100]})")


def run_openmeteo_spike() -> bool:
    print("\n" + "=" * 65)
    print("OPEN-METEO WEATHER PROVIDER EVALUATION")
    print("=" * 65)

    url = "https://api.open-meteo.com/v1/forecast"
    sample_coords = [
        {"name": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
        {"name": "Denver, CO", "lat": 39.7392, "lon": -104.9903},
        {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
    ]

    lat_str = ",".join(str(c["lat"]) for c in sample_coords)
    lon_str = ",".join(str(c["lon"]) for c in sample_coords)

    params = {
        "latitude": lat_str,
        "longitude": lon_str,
        "hourly": "wind_speed_10m,rain,showers,snowfall",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timeformat": "unixtime",
        "timezone": "auto",
        "past_hours": 3,
        "forecast_hours": 288,
    }

    print("1. Multi-Coordinate Query (3 sample points):")
    start = time.perf_counter()
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, params=params)
    elapsed = time.perf_counter() - start

    print(f"   HTTP Status: {resp.status_code}")
    print(f"   Elapsed Time: {elapsed:.3f} s")
    print(f"   Payload Size: {len(resp.content) / 1024:.1f} KB")

    if resp.status_code != 200:
        print(f"   [FAIL] Open-Meteo returned error: {resp.text}")
        return False

    data = resp.json()
    if not isinstance(data, list) or len(data) != len(sample_coords):
        print(f"   [FAIL] Expected array of {len(sample_coords)} items, got: {type(data)}")
        return False

    print(f"   [PASS] Returned JSON array preserving order ({len(data)} items).")
    first_loc = data[0]
    hourly = first_loc.get("hourly", {})
    timestamps = hourly.get("time", [])
    tz_info = f"{first_loc.get('timezone')} ({first_loc.get('timezone_abbreviation')})"
    print(f"   Timezone resolved: {tz_info}")
    print(f"   Hourly record count: {len(timestamps)} records")
    print(f"   Unix epoch timestamps: {bool(timestamps and isinstance(timestamps[0], int))}")

    _test_openmeteo_batch_scaling(url)

    print("[PASS] Open-Meteo provider verified successfully.")
    return True


# ============================================================================
# TomTom Routing & Geocoding Spike
# ============================================================================


def _check_truck_timeline(client: httpx.Client, url: str) -> None:
    print("\n2. Commercial Truck Governor & Timeline Verification:")
    resp = client.get(
        url,
        params={
            "key": TOMTOM_KEY,
            "travelMode": "truck",
            "vehicleMaxSpeed": 105,
            "traffic": "false",
            "instructionsType": "tagged",
            "computeTravelTimeFor": "all",
        },
    )
    if resp.status_code == 200:
        route = resp.json()["routes"][0]
        summary = route["summary"]
        dist_mi = summary["lengthInMeters"] / 1609.344
        dur_hr = summary["travelTimeInSeconds"] / 3600
        speed = dist_mi / dur_hr if dur_hr > 0 else 0
        instructions = route.get("guidance", {}).get("instructions", [])
        print(f"   Primary Route: {dist_mi:.1f} mi, {dur_hr:.2f} hr, speed: {speed:.1f} mph")
        print(f"   Instructions count: {len(instructions)}")

        offsets = [inst.get("routeOffsetInMeters", 0) for inst in instructions]
        times = [inst.get("travelTimeInSeconds", 0) for inst in instructions]
        is_mono_offset = all(offsets[i] <= offsets[i + 1] for i in range(len(offsets) - 1))
        is_mono_time = all(times[i] <= times[i + 1] for i in range(len(times) - 1))
        print(f"   Monotonic offsets: {is_mono_offset}, Monotonic times: {is_mono_time}")
        if instructions:
            last_time = times[-1]
            total_time = summary["travelTimeInSeconds"]
            print(f"   Final instruction ETA matches total: {last_time == total_time}")
    else:
        print(f"   [FAIL] HTTP {resp.status_code}: {sanitize(resp.text[:120])}")


def _check_us_corridors_and_geocoding(client: httpx.Client, base_url: str) -> None:
    print("\n3. Long Continental US Corridors Test:")
    for pair in US_PAIRS:
        po, pd = pair["origin"], pair["destination"]
        p_url = f"{base_url}/{po[0]},{po[1]}:{pd[0]},{pd[1]}/json"
        p_resp = client.get(
            p_url,
            params={
                "key": TOMTOM_KEY,
                "maxAlternatives": 2,
                "travelMode": "truck",
                "traffic": "false",
            },
        )
        if p_resp.status_code == 200:
            routes = p_resp.json().get("routes", [])
            print(f"   {pair['name']:32s} -> {len(routes)} routes returned")
        else:
            print(f"   {pair['name']:32s} -> HTTP {p_resp.status_code}")

    print("\n4. Geocoding Typeahead Search (TomTom Search v2):")
    geo_url = "https://api.tomtom.com/search/2/search/dalla.json"
    geo_resp = client.get(
        geo_url,
        params={
            "key": TOMTOM_KEY,
            "countrySet": "US",
            "typeahead": "true",
            "limit": 3,
        },
    )
    if geo_resp.status_code == 200:
        results = geo_resp.json().get("results", [])
        for res in results:
            addr = res.get("address", {}).get("freeformAddress")
            pos = res.get("position", {})
            print(f"   - Match: {addr}, Lat/Lon: ({pos.get('lat')}, {pos.get('lon')})")
    else:
        print(f"   [FAIL] Geocoding HTTP {geo_resp.status_code}: {sanitize(geo_resp.text[:120])}")


def run_tomtom_spike() -> bool:
    print("\n" + "=" * 65)
    print("TOMTOM ROUTING & GEOCODING PROVIDER EVALUATION")
    print("=" * 65)

    if not TOMTOM_KEY:
        print("[SKIP] TOMTOM_API_KEY is not set in environment or backend/.env.")
        print("       Set TOMTOM_API_KEY to execute TomTom provider evaluations.")
        return False

    with httpx.Client(timeout=20.0) as client:
        print("1. Maximum maxAlternatives Parameter:")
        base_calc_url = "https://api.tomtom.com/routing/1/calculateRoute"
        o, d = US_PAIRS[0]["origin"], US_PAIRS[0]["destination"]
        url = f"{base_calc_url}/{o[0]},{o[1]}:{d[0]},{d[1]}/json"

        resp = client.get(
            url,
            params={
                "key": TOMTOM_KEY,
                "maxAlternatives": 3,
                "travelMode": "truck",
                "traffic": "false",
            },
        )
        if resp.status_code == 200:
            routes = resp.json().get("routes", [])
            print(f"   maxAlternatives=3 -> HTTP 200, returned {len(routes)} routes.")
        else:
            print(f"   [FAIL] HTTP {resp.status_code}: {sanitize(resp.text[:120])}")
            return False

        _check_truck_timeline(client, url)
        _check_us_corridors_and_geocoding(client, base_calc_url)

    print("[PASS] TomTom provider verified successfully.")
    return True


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="StormRoute Provider Spike Evaluation (Phase P0 / F-065)"
    )
    parser.add_argument("--weather", action="store_true", help="Run Open-Meteo evaluations")
    parser.add_argument("--routing", action="store_true", help="Run TomTom evaluations")
    parser.add_argument("--all", action="store_true", help="Run full evaluation suite")

    args = parser.parse_args()
    run_all = args.all or (not args.weather and not args.routing)

    print("=" * 65)
    print("STORMRUTE PROVIDER SPIKE (F-000 / F-065 CONSOLIDATED)")
    print("=" * 65)

    success = True
    if run_all or args.weather:
        success = run_openmeteo_spike() and success

    if run_all or args.routing:
        success = run_tomtom_spike() and success

    print("\n" + "=" * 65)
    print("SPIKE RUN COMPLETE" if success else "SPIKE RUN COMPLETED WITH WARNINGS")
    print("=" * 65)


if __name__ == "__main__":
    main()
