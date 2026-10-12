"""
Deep P0 Provider Investigation Script for StormRoute.
Covers:
1. Exact ARCHITECTURE.md §6 Fallback test on Dallas->Denver and Chicago->Atlanta:
   - Anchor at 33% and 66% along fastest route polyline.
   - Perpendicular offset clamp(0.12 * route_miles, 15, 60) on both sides (+90 deg and -90 deg).
   - Route origin -> via -> destination.
   - Check if TomTom snaps via point to existing road.
   - 1-mile sampling overlap check: fraction of length within 0.3 mi of Route 1 and Route 2.
   - Check criteria: overlap < 85%, duration < 1.6x fastest.
2. Implied average speed of all routes & effect of vehicleMaxSpeed and other truck parameters.
3. Instruction travelTimeInSeconds cumulative verification (monotonic, final value vs total duration).
4. Geocoding typeahead test with countrySet=US for 'dalla' and 'denv'.
"""

import math
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

EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def destination_point(lat: float, lon: float, bearing_deg: float, distance_miles: float) -> tuple[float, float]:
    r = EARTH_RADIUS_MILES
    d_r = distance_miles / r
    theta = math.radians(bearing_deg)
    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)

    phi2 = math.asin(math.sin(phi1) * math.cos(d_r) + math.cos(phi1) * math.sin(d_r) * math.cos(theta))
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(d_r) * math.cos(phi1),
        math.cos(d_r) - math.sin(phi1) * math.sin(phi2)
    )
    return math.degrees(phi2), math.degrees(lambda2)


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def polyline_cumulative_distances(pts: list[tuple[float, float]]) -> list[float]:
    cum = [0.0]
    for i in range(1, len(pts)):
        d = haversine_miles(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
        cum.append(cum[-1] + d)
    return cum


def point_at_fraction(pts: list[tuple[float, float]], cum: list[float], frac: float) -> tuple[tuple[float, float], float]:
    """Returns ((lat, lon), local_bearing) at distance fraction."""
    target_dist = frac * cum[-1]
    for i in range(1, len(cum)):
        if cum[i] >= target_dist:
            seg_len = cum[i] - cum[i - 1]
            seg_t = (target_dist - cum[i - 1]) / seg_len if seg_len > 0 else 0.0
            lat = pts[i - 1][0] + seg_t * (pts[i][0] - pts[i - 1][0])
            lon = pts[i - 1][1] + seg_t * (pts[i][1] - pts[i - 1][1])
            # Local bearing
            b = bearing_deg(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
            return (lat, lon), b
    return pts[-1], 0.0


def sample_polyline_every_mile(pts: list[tuple[float, float]], interval_miles: float = 1.0) -> list[tuple[float, float]]:
    cum = polyline_cumulative_distances(pts)
    total_len = cum[-1]
    samples = []
    curr = 0.0
    while curr <= total_len:
        # find point at curr
        for i in range(1, len(cum)):
            if cum[i] >= curr:
                seg_len = cum[i] - cum[i - 1]
                t = (curr - cum[i - 1]) / seg_len if seg_len > 0 else 0.0
                lat = pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0])
                lon = pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])
                samples.append((lat, lon))
                break
        curr += interval_miles
    return samples


def min_dist_to_polyline(pt: tuple[float, float], pts: list[tuple[float, float]]) -> float:
    # fast approximation: min distance to polyline vertices
    # for fine resolution polylines (>8,000 vertices), vertex distance is accurate to within a few meters
    min_d = float("inf")
    lat, lon = pt
    for plat, plon in pts:
        d = haversine_miles(lat, lon, plat, plon)
        if d < min_d:
            min_d = d
            if min_d < 0.1:
                break
    return min_d


def compute_overlap_fraction(candidate_pts: list[tuple[float, float]], reference_pts: list[tuple[float, float]], threshold_mi: float = 0.3) -> float:
    samples = sample_polyline_every_mile(candidate_pts, interval_miles=1.0)
    if not samples:
        return 0.0
    within = 0
    for s in samples:
        if min_dist_to_polyline(s, reference_pts) <= threshold_mi:
            within += 1
    return within / len(samples)


# -------------------------------------------------------------
# Test 1: Fallback Test on Dallas->Denver and Chicago->Atlanta
# -------------------------------------------------------------
def run_fallback_test(client: httpx.Client, key: str):
    print("=" * 70)
    print("1. ARCHITECTURE.MD §6 FALLBACK TEST (Dallas->Denver & Chicago->Atlanta)")
    print("=" * 70)

    pairs = [
        {"name": "Dallas -> Denver", "origin": (32.7767, -96.7970), "dest": (39.7392, -104.9903)},
        {"name": "Chicago -> Atlanta", "origin": (41.8781, -87.6298), "dest": (33.7490, -84.3880)},
    ]

    base_url = "https://api.tomtom.com/routing/1/calculateRoute"

    results = []

    for p in pairs:
        print(f"\n--- Testing Pair: {p['name']} ---")
        orig, dest = p["origin"], p["dest"]
        url_base = f"{base_url}/{orig[0]},{orig[1]}:{dest[0]},{dest[1]}/json"

        # 1. Get initial routes
        resp = client.get(url_base, params={"key": key, "maxAlternatives": 2, "travelMode": "truck"})
        if resp.status_code != 200:
            print(f"Failed to fetch initial routes: HTTP {resp.status_code}")
            continue

        init_routes = resp.json()["routes"]
        print(f"Initial routes returned: {len(init_routes)}")
        init_polylines = []
        for idx, r in enumerate(init_routes):
            s = r["summary"]
            pts = [(pt["latitude"], pt["longitude"]) for leg in r["legs"] for pt in leg["points"]]
            dist_mi = s["lengthInMeters"] * 0.000621371
            dur_s = s["travelTimeInSeconds"]
            dur_h = dur_s / 3600
            init_polylines.append(pts)
            print(f"  Existing Route #{idx+1}: {dist_mi:.1f} mi, {dur_h:.2f} hrs ({dur_s}s), {len(pts)} pts")

        fastest_route = min(init_routes, key=lambda r: r["summary"]["travelTimeInSeconds"])
        fastest_pts = [(pt["latitude"], pt["longitude"]) for leg in fastest_route["legs"] for pt in leg["points"]]
        fastest_dist_mi = fastest_route["summary"]["lengthInMeters"] * 0.000621371
        fastest_dur_s = fastest_route["summary"]["travelTimeInSeconds"]

        cum_dist = polyline_cumulative_distances(fastest_pts)
        offset_distance = max(15.0, min(60.0, 0.12 * fastest_dist_mi))
        print(f"Fastest distance: {fastest_dist_mi:.1f} mi, offset distance: clamp(0.12 * {fastest_dist_mi:.1f}, 15, 60) = {offset_distance:.1f} mi")

        anchors = [0.33, 0.66]
        sides = [("Left (+90 deg)", 90), ("Right (-90 deg)", -90)]

        pair_fallback_results = []
        found_distinct_third = False

        for anchor_frac in anchors:
            anchor_pt, heading = point_at_fraction(fastest_pts, cum_dist, anchor_frac)
            print(f"\nAnchor at {int(anchor_frac*100)}%: lat={anchor_pt[0]:.4f}, lon={anchor_pt[1]:.4f}, heading={heading:.1f}°")

            for side_name, side_angle in sides:
                perp_bearing = (heading + side_angle) % 360
                via_lat, via_lon = destination_point(anchor_pt[0], anchor_pt[1], perp_bearing, offset_distance)

                # Query origin -> via -> destination
                url_via = f"{base_url}/{orig[0]},{orig[1]}:{via_lat:.5f},{via_lon:.5f}:{dest[0]},{dest[1]}/json"
                resp_via = client.get(url_via, params={"key": key, "travelMode": "truck"})

                if resp_via.status_code != 200:
                    print(f"  [{side_name}] Route failed: HTTP {resp_via.status_code}")
                    continue

                via_route = resp_via.json()["routes"][0]
                s = via_route["summary"]
                dist_mi = s["lengthInMeters"] * 0.000621371
                dur_s = s["travelTimeInSeconds"]
                dur_h = dur_s / 3600
                duration_ratio = dur_s / fastest_dur_s

                candidate_pts = [(pt["latitude"], pt["longitude"]) for leg in via_route["legs"] for pt in leg["points"]]

                # Check if TomTom snapped via point back to the same road:
                # Leg 0 end point vs requested via point:
                leg0_end = via_route["legs"][0]["points"][-1]
                snap_dist = haversine_miles(via_lat, via_lon, leg0_end["latitude"], leg0_end["longitude"])
                dist_to_fastest_at_via = min_dist_to_polyline((via_lat, via_lon), fastest_pts)

                # Compute overlaps with existing routes
                overlap_r1 = compute_overlap_fraction(candidate_pts, init_polylines[0], threshold_mi=0.3)
                overlap_r2 = compute_overlap_fraction(candidate_pts, init_polylines[1], threshold_mi=0.3) if len(init_polylines) > 1 else 0.0
                max_overlap = max(overlap_r1, overlap_r2)

                is_distinct = (max_overlap < 0.85) and (duration_ratio < 1.6)

                print(f"  [{side_name} offset {offset_distance:.1f} mi]:")
                print(f"    Via Point target: ({via_lat:.4f}, {via_lon:.4f}) | Distance to highway: {dist_to_fastest_at_via:.1f} mi | Snap dist to nearest road: {snap_dist:.2f} mi")
                print(f"    Result: {dist_mi:.1f} mi, {dur_h:.2f} hrs ({dur_s}s), duration ratio: {duration_ratio:.2f}x")
                print(f"    Overlap with Route 1: {overlap_r1*100:.1f}%, Route 2: {overlap_r2*100:.1f}% -> Max Overlap: {max_overlap*100:.1f}%")
                print(f"    Distinct 3rd route qualified (<85% overlap & <1.6x time)? {'YES [PASS]' if is_distinct else 'NO'}")

                pair_fallback_results.append({
                    "anchor": f"{int(anchor_frac*100)}%",
                    "side": side_name,
                    "offset_mi": round(offset_distance, 1),
                    "dist_mi": round(dist_mi, 1),
                    "duration_h": round(dur_h, 2),
                    "duration_ratio": round(duration_ratio, 2),
                    "overlap_r1_pct": round(overlap_r1 * 100, 1),
                    "overlap_r2_pct": round(overlap_r2 * 100, 1),
                    "max_overlap_pct": round(max_overlap * 100, 1),
                    "snap_distance_mi": round(snap_dist, 2),
                    "is_distinct": is_distinct
                })

                if is_distinct:
                    found_distinct_third = True

        results.append({
            "pair": p["name"],
            "found_distinct_third": found_distinct_third,
            "trials": pair_fallback_results
        })

    return results


# -------------------------------------------------------------
# Test 2: Implied Average Speed & Optional Truck Parameters
# -------------------------------------------------------------
def run_speed_and_truck_params_test(client: httpx.Client, key: str):
    print("\n" + "=" * 70)
    print("2. IMPLIED AVERAGE SPEED & OPTIONAL TRUCK PARAMETERS")
    print("=" * 70)

    # 4 US pairs implied speed
    pairs_data = [
        {"name": "Dallas -> Denver Route 1", "dist_mi": 882.3, "dur_s": 42682},
        {"name": "Dallas -> Denver Route 2", "dist_mi": 798.5, "dur_s": 44280},
        {"name": "LA -> Salt Lake City Route 1", "dist_mi": 688.4, "dur_s": 35621},
        {"name": "LA -> Salt Lake City Route 2", "dist_mi": 792.8, "dur_s": 48187},
        {"name": "LA -> Salt Lake City Route 3", "dist_mi": 1037.0, "dur_s": 56244},
        {"name": "Chicago -> Atlanta Route 1", "dist_mi": 715.8, "dur_s": 37870},
        {"name": "Chicago -> Atlanta Route 2", "dist_mi": 754.4, "dur_s": 39313},
        {"name": "Seattle -> Boise Route 1", "dist_mi": 506.0, "dur_s": 27160},
        {"name": "Seattle -> Boise Route 2", "dist_mi": 500.8, "dur_s": 29314},
        {"name": "Seattle -> Boise Route 3", "dist_mi": 596.6, "dur_s": 32116},
    ]

    print("Implied average speeds across all previously tested routes:")
    for pd in pairs_data:
        speed_mph = pd["dist_mi"] / (pd["dur_s"] / 3600)
        print(f"  {pd['name']}: {pd['dist_mi']} mi / {pd['dur_s']/3600:.2f} h = {speed_mph:.1f} mph")

    # Testing vehicleMaxSpeed and other truck parameters on Dallas->Denver
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"
    url = f"{base_url}/32.7767,-96.7970:39.7392,-104.9903/json"

    print("\nTesting parameter sensitivity on Dallas -> Denver:")
    param_variations = [
        ("Baseline (travelMode=truck only)", {"travelMode": "truck"}),
        ("vehicleMaxSpeed=90 (km/h ~ 56 mph)", {"travelMode": "truck", "vehicleMaxSpeed": 90}),
        ("vehicleMaxSpeed=105 (km/h ~ 65 mph)", {"travelMode": "truck", "vehicleMaxSpeed": 105}),
        ("vehicleMaxSpeed=120 (km/h ~ 75 mph)", {"travelMode": "truck", "vehicleMaxSpeed": 120}),
        ("vehicleCommercial=true", {"travelMode": "truck", "vehicleCommercial": "true"}),
        ("vehicleWeight=36287 (kg ~ 80k lb)", {"travelMode": "truck", "vehicleWeight": 36287}),
        ("vehicleAxleWeight=9071 (kg ~ 20k lb)", {"travelMode": "truck", "vehicleAxleWeight": 9071}),
        ("vehicleLength=21.3 (meters ~ 70 ft)", {"travelMode": "truck", "vehicleLength": 21.3}),
    ]

    param_results = []
    for label, extra_p in param_variations:
        p = {"key": key, **extra_p}
        resp = client.get(url, params=p)
        if resp.status_code == 200:
            s = resp.json()["routes"][0]["summary"]
            dist_mi = s["lengthInMeters"] * 0.000621371
            dur_s = s["travelTimeInSeconds"]
            dur_h = dur_s / 3600
            avg_spd = dist_mi / dur_h
            print(f"  {label}: {dist_mi:.1f} mi, {dur_h:.2f} hrs ({dur_s}s), avg {avg_spd:.1f} mph")
            param_results.append({"label": label, "status": 200, "dist_mi": round(dist_mi, 1), "dur_h": round(dur_h, 2), "dur_s": dur_s, "avg_mph": round(avg_spd, 1)})
        else:
            print(f"  {label}: HTTP {resp.status_code}")
            param_results.append({"label": label, "status": resp.status_code, "error": resp.text[:100]})

    return param_results


# -------------------------------------------------------------
# Test 3: Cumulative Instruction Travel Time Verification
# -------------------------------------------------------------
def run_instruction_cumulative_test(client: httpx.Client, key: str):
    print("\n" + "=" * 70)
    print("3. INSTRUCTION TRAVEL TIME CUMULATIVE & MONOTONIC TEST")
    print("=" * 70)
    base_url = "https://api.tomtom.com/routing/1/calculateRoute"

    test_pairs = [
        ("Dallas -> Denver", (32.7767, -96.7970), (39.7392, -104.9903)),
        ("Chicago -> Atlanta", (41.8781, -87.6298), (33.7490, -84.3880)),
    ]

    results = []
    for name, orig, dest in test_pairs:
        url = f"{base_url}/{orig[0]},{orig[1]}:{dest[0]},{dest[1]}/json"
        params = {
            "key": key,
            "travelMode": "truck",
            "instructionsType": "tagged",
            "computeTravelTimeFor": "all",
        }
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            print(f"  {name}: HTTP {resp.status_code}")
            continue

        route = resp.json()["routes"][0]
        total_dur_s = route["summary"]["travelTimeInSeconds"]
        total_dist_m = route["summary"]["lengthInMeters"]
        instructions = route.get("guidance", {}).get("instructions", [])

        print(f"\n{name}: Total route duration = {total_dur_s}s, instructions count = {len(instructions)}")

        is_monotonic_time = True
        is_monotonic_dist = True
        prev_time = -1
        prev_dist = -1

        for i, inst in enumerate(instructions):
            t = inst.get("travelTimeInSeconds", 0)
            d = inst.get("routeOffsetInMeters", 0)
            if t < prev_time:
                is_monotonic_time = False
                print(f"  [VIOLATION] Decreasing time at #{i}: {t} < {prev_time}")
            if d < prev_dist:
                is_monotonic_dist = False
                print(f"  [VIOLATION] Decreasing distance at #{i}: {d} < {prev_dist}")
            prev_time = t
            prev_dist = d

        last_inst = instructions[-1] if instructions else {}
        last_t = last_inst.get("travelTimeInSeconds", 0)
        last_d = last_inst.get("routeOffsetInMeters", 0)
        time_diff = abs(total_dur_s - last_t)
        dist_diff = abs(total_dist_m - last_d)

        print(f"  Monotonic non-decreasing time? {'YES [PASS]' if is_monotonic_time else 'NO [FAIL]'}")
        print(f"  Monotonic non-decreasing distance? {'YES [PASS]' if is_monotonic_dist else 'NO [FAIL]'}")
        print(f"  Last instruction time: {last_t}s vs Route total: {total_dur_s}s (diff: {time_diff}s)")
        print(f"  Last instruction distance: {last_d}m vs Route total: {total_dist_m}m (diff: {dist_diff}m)")
        print(f"  Match status: {'EXACT MATCH [PASS]' if time_diff == 0 else f'Close (delta={time_diff}s)'}")

        results.append({
            "pair": name,
            "instructions_count": len(instructions),
            "is_monotonic_time": is_monotonic_time,
            "is_monotonic_dist": is_monotonic_dist,
            "total_dur_s": total_dur_s,
            "last_t": last_t,
            "time_diff_s": time_diff,
            "total_dist_m": total_dist_m,
            "last_d": last_d,
            "dist_diff_m": dist_diff,
        })

    return results


# -------------------------------------------------------------
# Test 4: Geocoding with countrySet=US
# -------------------------------------------------------------
def run_geocoding_country_set_test(client: httpx.Client, key: str):
    print("\n" + "=" * 70)
    print("4. GEOCODING TYPEAHEAD TEST WITH countrySet=US")
    print("=" * 70)

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

        print(f"\nQuery: '{q}' (HTTP {resp.status_code}, {elapsed:.2f}s):")
        hits_info = []
        if resp.status_code == 200:
            results_list = resp.json().get("results", [])
            for idx, item in enumerate(results_list):
                addr = item.get("address", {})
                freeform = addr.get("freeformAddress", "")
                country = addr.get("countryCode", "")
                country_sub = addr.get("countrySubdivision", "")
                pos = item.get("position", {})
                print(f"  #{idx+1}: {freeform} [{country_sub}, {country}] (lat: {pos.get('lat')}, lon: {pos.get('lon')})")
                hits_info.append({
                    "address": freeform,
                    "state": country_sub,
                    "country": country,
                    "lat": pos.get("lat"),
                    "lon": pos.get("lon"),
                })
            results[q] = hits_info
        else:
            print(f"  Error: {resp.text[:150]}")
    return results


def main():
    if not TOMTOM_KEY:
        print("[ERROR] TOMTOM_API_KEY is missing from environment.")
        sys.exit(1)

    print("Beginning Deep Investigation for P0...")
    with httpx.Client(timeout=30.0) as client:
        fb_results = run_fallback_test(client, TOMTOM_KEY)
        spd_results = run_speed_and_truck_params_test(client, TOMTOM_KEY)
        inst_results = run_instruction_cumulative_test(client, TOMTOM_KEY)
        geo_results = run_geocoding_country_set_test(client, TOMTOM_KEY)


if __name__ == "__main__":
    main()
