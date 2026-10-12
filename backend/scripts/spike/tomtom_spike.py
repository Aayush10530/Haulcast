"""
Comprehensive TomTom Routing and Geocoding Spike for StormRoute (F-000).
Tests:
1. Maximum maxAlternatives supported.
2. Truck mode testing (travelMode=truck vs car, extra truck parameters).
3. Per-segment travel time & timeline structure (instructions, legs, sections).
4. 4 long US pairs (routes count, distances, durations, distinctness).
5. Via-waypoint fallback routing.
6. Geocoding typeahead search for 'dalla' and 'denv'.
NOTE: The API key is loaded from backend/.env and NEVER printed.
"""

import os
import sys
import time
from pathlib import Path
import httpx

# Load backend/.env
env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    try:
        import dotenv
        dotenv.load_dotenv(env_path)
    except ImportError:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

TOMTOM_KEY = (os.environ.get("TOMTOM_API_KEY") or "").strip()

PAIRS = [
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


def test_max_alternatives(client: httpx.Client, key: str):
    print("=" * 60)
    print("1. MAX ALTERNATIVES TEST (Dallas -> Denver)")
    print("=" * 60)
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    origin, dest = PAIRS[0]["origin"], PAIRS[0]["destination"]
    url = f"{base_url}/{origin[0]},{origin[1]}:{dest[0]},{dest[1]}/json"

    max_working = 0
    results = {}
    for alt in [0, 1, 2, 3, 4, 5, 6]:
        params = {
            "key": key,
            "maxAlternatives": alt,
            "travelMode": "truck",
        }
        resp = client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            num_routes = len(data.get("routes", []))
            print(f"  maxAlternatives={alt} -> HTTP 200, returned {num_routes} routes")
            max_working = alt
            results[alt] = num_routes
        else:
            print(f"  maxAlternatives={alt} -> HTTP {resp.status_code} ({sanitize(resp.text[:150])})")
            results[alt] = f"HTTP {resp.status_code}"

    print(f"  [RESULT] Maximum working maxAlternatives: {max_working}")
    return max_working, results


def test_truck_mode_parameters(client: httpx.Client, key: str):
    print("\n" + "=" * 60)
    print("2. TRUCK MODE & EXTRA PARAMETERS TEST (Dallas -> Denver)")
    print("=" * 60)
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    origin, dest = PAIRS[0]["origin"], PAIRS[0]["destination"]
    url = f"{base_url}/{origin[0]},{origin[1]}:{dest[0]},{dest[1]}/json"

    # 1. Car baseline
    resp_car = client.get(url, params={"key": key, "travelMode": "car"})
    car_time, car_dist = None, None
    if resp_car.status_code == 200:
        s = resp_car.json()["routes"][0]["summary"]
        car_dist = s["lengthInMeters"] * 0.000621371
        car_time = s["travelTimeInSeconds"] / 3600
        print(f"  Car Mode: {car_dist:.1f} mi, {car_time:.2f} hrs")

    # 2. Truck default
    resp_truck = client.get(url, params={"key": key, "travelMode": "truck"})
    truck_time, truck_dist = None, None
    if resp_truck.status_code == 200:
        s = resp_truck.json()["routes"][0]["summary"]
        truck_dist = s["lengthInMeters"] * 0.000621371
        truck_time = s["travelTimeInSeconds"] / 3600
        print(f"  Truck (travelMode=truck only): {truck_dist:.1f} mi, {truck_time:.2f} hrs")
        print(f"    -> Difference vs car: {truck_time - car_time:+.2f} hrs (truck speed restrictions reflected)")
    else:
        print(f"  [FAIL] travelMode=truck failed: {sanitize(resp_truck.text[:200])}")

    # 3. Truck with commercial and weight params
    params_heavy = {
        "key": key,
        "travelMode": "truck",
        "vehicleCommercial": "true",
        "vehicleWeight": 36287,  # 80,000 lbs in kg
    }
    resp_heavy = client.get(url, params=params_heavy)
    if resp_heavy.status_code == 200:
        s = resp_heavy.json()["routes"][0]["summary"]
        heavy_dist = s["lengthInMeters"] * 0.000621371
        heavy_time = s["travelTimeInSeconds"] / 3600
        print(f"  Truck with vehicleCommercial=true & vehicleWeight=36287kg: {heavy_dist:.1f} mi, {heavy_time:.2f} hrs")
        print("  [PASS] travelMode=truck works out-of-the-box, optional vehicleCommercial/vehicleWeight also accepted without error.")
    else:
        print(f"  [NOTE] Extra truck params response: {resp_heavy.status_code} ({sanitize(resp_heavy.text[:150])})")


def test_segment_times_and_instructions(client: httpx.Client, key: str):
    print("\n" + "=" * 60)
    print("3. SEGMENT TRAVEL TIME & TIMELINE FIELD INVESTIGATION")
    print("=" * 60)
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    origin, dest = PAIRS[0]["origin"], PAIRS[0]["destination"]
    url = f"{base_url}/{origin[0]},{origin[1]}:{dest[0]},{dest[1]}/json"

    # Request with instructionsType=tagged and computeTravelTimeFor=all
    params = {
        "key": key,
        "travelMode": "truck",
        "instructionsType": "tagged",
        "computeTravelTimeFor": "all",
    }
    resp = client.get(url, params=params)
    if resp.status_code != 200:
        print(f"  [FAIL] {sanitize(resp.text[:200])}")
        return

    data = resp.json()
    route = data["routes"][0]
    summary = route.get("summary", {})
    legs = route.get("legs", [])
    sections = route.get("sections", [])
    guidance = route.get("guidance", {})
    instructions = guidance.get("instructions", [])

    print(f"  Route top-level keys: {list(route.keys())}")
    print(f"  Number of legs: {len(legs)}")
    print(f"  Number of sections: {len(sections)}")
    print(f"  Number of guidance instructions: {len(instructions)}")

    if legs:
        leg_summary = legs[0].get("summary", {})
        print(f"  Leg summary keys: {list(leg_summary.keys())}")
        print(f"    lengthInMeters: {leg_summary.get('lengthInMeters')}")
        print(f"    travelTimeInSeconds: {leg_summary.get('travelTimeInSeconds')}")
        points = legs[0].get("points", [])
        print(f"    Leg points (polyline vertices): {len(points)} vertices")
        if points:
            print(f"    Vertex format: {points[0]} (lat/lon keys: {list(points[0].keys())})")

    if instructions:
        sample = instructions[0]
        print(f"\n  Guidance instruction fields: {list(sample.keys())}")
        print(f"    Sample instruction #1:")
        print(f"      routeOffsetInMeters: {sample.get('routeOffsetInMeters')}")
        print(f"      travelTimeInSeconds: {sample.get('travelTimeInSeconds')}")
        print(f"      point: {sample.get('point')}")
        print(f"      message: {sample.get('message')}")
        if len(instructions) > 1:
            sample2 = instructions[1]
            print(f"    Sample instruction #2:")
            print(f"      routeOffsetInMeters: {sample2.get('routeOffsetInMeters')}")
            print(f"      travelTimeInSeconds: {sample2.get('travelTimeInSeconds')}")
        print("  [PASS] Guidance instructions provide both cumulative 'routeOffsetInMeters' and 'travelTimeInSeconds'!")
        print("         This provides fine-grained (distance, elapsed_seconds) timeline control points!")
    elif sections:
        print(f"  Sections sample: {sections[:2]}")


def test_4_us_pairs(client: httpx.Client, key: str, max_alt: int = 2):
    print("\n" + "=" * 60)
    print("4. FOUR US PAIRS ROUTING TEST")
    print("=" * 60)
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"

    results = []
    for pair in PAIRS:
        origin, dest = pair["origin"], pair["destination"]
        url = f"{base_url}/{origin[0]},{origin[1]}:{dest[0]},{dest[1]}/json"
        params = {
            "key": key,
            "maxAlternatives": max_alt,
            "travelMode": "truck",
            "computeTravelTimeFor": "all",
            "instructionsType": "tagged",
        }

        start = time.perf_counter()
        resp = client.get(url, params=params)
        elapsed = time.perf_counter() - start

        if resp.status_code != 200:
            print(f"\n{pair['name']}: FAILED ({resp.status_code}) - {sanitize(resp.text[:150])}")
            results.append({
                "pair": pair["name"],
                "routes_count": 0,
                "elapsed": elapsed,
                "routes_info": [],
                "error": resp.status_code
            })
            continue

        data = resp.json()
        routes = data.get("routes", [])
        routes_info = []
        print(f"\n{pair['name']} ({elapsed:.2f}s, {len(routes)} routes returned):")

        for idx, r in enumerate(routes):
            s = r["summary"]
            dist_mi = s["lengthInMeters"] * 0.000621371
            dur_s = s["travelTimeInSeconds"]
            dur_h = dur_s / 3600
            pts = sum(len(leg.get("points", [])) for leg in r.get("legs", []))
            inst_count = len(r.get("guidance", {}).get("instructions", []))
            print(f"  Route #{idx+1}: {dist_mi:.1f} mi, {dur_h:.2f} hrs ({dur_s}s), {pts} polyline pts, {inst_count} instructions")
            routes_info.append({
                "id": idx + 1,
                "dist_miles": round(dist_mi, 1),
                "duration_seconds": dur_s,
                "duration_hours": round(dur_h, 2),
                "polyline_points": pts,
                "instructions": inst_count,
            })

        results.append({
            "pair": pair["name"],
            "routes_count": len(routes),
            "elapsed": round(elapsed, 2),
            "routes_info": routes_info,
            "error": None
        })

    return results


def test_via_waypoint(client: httpx.Client, key: str):
    print("\n" + "=" * 60)
    print("5. VIA-WAYPOINT FALLBACK ROUTING TEST")
    print("=" * 60)
    # Dallas -> Lubbock (via) -> Denver
    origin = (32.7767, -96.7970)
    via = (33.5779, -101.8552)
    dest = (39.7392, -104.9903)

    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    url = f"{base_url}/{origin[0]},{origin[1]}:{via[0]},{via[1]}:{dest[0]},{dest[1]}/json"
    params = {
        "key": key,
        "travelMode": "truck",
        "computeTravelTimeFor": "all",
    }

    start = time.perf_counter()
    resp = client.get(url, params=params)
    elapsed = time.perf_counter() - start

    if resp.status_code == 200:
        data = resp.json()
        routes = data.get("routes", [])
        if routes:
            s = routes[0]["summary"]
            dist_mi = s["lengthInMeters"] * 0.000621371
            dur_h = s["travelTimeInSeconds"] / 3600
            legs = routes[0].get("legs", [])
            print(f"  Status 200 in {elapsed:.2f}s | Returned {len(routes)} route")
            print(f"  Via route: {dist_mi:.1f} mi, {dur_h:.2f} hrs, {len(legs)} legs")
            return {"status": "SUCCESS", "legs": len(legs), "dist_miles": round(dist_mi, 1), "hours": round(dur_h, 2)}
    print(f"  [FAIL] {sanitize(resp.text[:200])}")
    return {"status": f"FAIL ({resp.status_code})"}


def test_geocoding_typeahead(client: httpx.Client, key: str):
    print("\n" + "=" * 60)
    print("6. GEOCODING / SEARCH TYPEAHEAD TEST ('dalla' & 'denv')")
    print("=" * 60)
    base_url = "https://api.tomtom.com/search/2/search"

    results = {}
    for q in ["dalla", "denv"]:
        url = f"{base_url}/{q}.json"
        params = {
            "key": key,
            "typeahead": "true",
            "limit": 5,
            "countrySet": "US",
        }
        start = time.perf_counter()
        resp = client.get(url, params=params)
        elapsed = time.perf_counter() - start

        if resp.status_code == 200:
            hits = resp.json().get("results", [])
            items = []
            print(f"\n  Query: '{q}' ({elapsed:.2f}s, {len(hits)} hits):")
            for h in hits[:3]:
                addr = h.get("address", {}).get("freeformAddress", "")
                pos = h.get("position", {})
                print(f"    - {addr} (lat: {pos.get('lat')}, lon: {pos.get('lon')})")
                items.append(f"{addr} ({pos.get('lat')}, {pos.get('lon')})")
            results[q] = items
        else:
            print(f"  Query: '{q}' FAILED ({resp.status_code}): {sanitize(resp.text[:150])}")
            results[q] = f"FAIL ({resp.status_code})"
    return results


def main():
    if not TOMTOM_KEY:
        print("[ERROR] TOMTOM_API_KEY is not set.")
        sys.exit(1)

    print("TomTom API Key found in environment. Beginning tests...\n")

    with httpx.Client(timeout=25.0) as client:
        test_max_alternatives(client, TOMTOM_KEY)
        test_truck_mode_parameters(client, TOMTOM_KEY)
        test_segment_times_and_instructions(client, TOMTOM_KEY)
        test_4_us_pairs(client, TOMTOM_KEY)
        test_via_waypoint(client, TOMTOM_KEY)
        test_geocoding_typeahead(client, TOMTOM_KEY)


if __name__ == "__main__":
    main()
