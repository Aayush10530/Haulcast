"""
Final P0 Round Script for Haulcast.
Covers:
1. Determinism test: Dallas->Denver 3x default vs 3x traffic=false.
2. Standard test: all 4 US pairs with traffic=false and vehicleMaxSpeed=105.
   Fallback run with 4 parallel via requests for pairs with < 3 routes.
   Reports wall time, lowest-overlap qualifying candidate.
3. Instruction continuity test across legs on a via route (reset vs continuous, stitching).
"""

import concurrent.futures
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
BASE_URL = "https://api.tomtom.com/routing/1/calculateRoute"


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
    target_dist = frac * cum[-1]
    for i in range(1, len(cum)):
        if cum[i] >= target_dist:
            seg_len = cum[i] - cum[i - 1]
            seg_t = (target_dist - cum[i - 1]) / seg_len if seg_len > 0 else 0.0
            lat = pts[i - 1][0] + seg_t * (pts[i][0] - pts[i - 1][0])
            lon = pts[i - 1][1] + seg_t * (pts[i][1] - pts[i - 1][1])
            b = bearing_deg(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1])
            return (lat, lon), b
    return pts[-1], 0.0


def sample_polyline_every_mile(pts: list[tuple[float, float]], interval_miles: float = 1.0) -> list[tuple[float, float]]:
    cum = polyline_cumulative_distances(pts)
    total_len = cum[-1]
    samples = []
    curr = 0.0
    while curr <= total_len:
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
# 1. Determinism Test
# -------------------------------------------------------------
def test_determinism(client: httpx.Client, key: str):
    print("=" * 70)
    print("1. DETERMINISM TEST: DALLAS -> DENVER (3x Default vs 3x traffic=false)")
    print("=" * 70)
    orig, dest = (32.7767, -96.7970), (39.7392, -104.9903)
    url = f"{BASE_URL}/{orig[0]},{orig[1]}:{dest[0]},{dest[1]}/json"

    # Default runs
    print("\n--- 3 Runs with Default Settings (live traffic enabled by default) ---")
    default_runs = []
    for run in range(1, 4):
        p = {"key": key, "travelMode": "truck", "maxAlternatives": 2, "instructionsType": "tagged"}
        resp = client.get(url, params=p)
        data = resp.json()
        routes = data.get("routes", [])
        run_info = []
        for idx, r in enumerate(routes):
            s = r["summary"]
            run_info.append({
                "route_idx": idx + 1,
                "dist_mi": round(s["lengthInMeters"] * 0.000621371, 1),
                "dur_s": s["travelTimeInSeconds"],
                "dur_h": round(s["travelTimeInSeconds"] / 3600, 3),
                "inst_count": len(r.get("guidance", {}).get("instructions", [])),
            })
        default_runs.append(run_info)
        print(f"  Run #{run}: {len(routes)} routes returned | " +
              ", ".join([f"R{r['route_idx']}: {r['dist_mi']} mi, {r['dur_h']:.2f}h ({r['dur_s']}s)" for r in run_info]))
        time.sleep(0.5)

    # traffic=false runs
    print("\n--- 3 Runs with traffic=false ---")
    no_traffic_runs = []
    for run in range(1, 4):
        p = {"key": key, "travelMode": "truck", "traffic": "false", "maxAlternatives": 2, "instructionsType": "tagged"}
        resp = client.get(url, params=p)
        data = resp.json()
        routes = data.get("routes", [])
        run_info = []
        for idx, r in enumerate(routes):
            s = r["summary"]
            run_info.append({
                "route_idx": idx + 1,
                "dist_mi": round(s["lengthInMeters"] * 0.000621371, 1),
                "dur_s": s["travelTimeInSeconds"],
                "dur_h": round(s["travelTimeInSeconds"] / 3600, 3),
                "inst_count": len(r.get("guidance", {}).get("instructions", [])),
            })
        no_traffic_runs.append(run_info)
        print(f"  Run #{run}: {len(routes)} routes returned | " +
              ", ".join([f"R{r['route_idx']}: {r['dist_mi']} mi, {r['dur_h']:.2f}h ({r['dur_s']}s)" for r in run_info]))
        time.sleep(0.5)

    return default_runs, no_traffic_runs


# -------------------------------------------------------------
# 2. 4 US Pairs with traffic=false & vehicleMaxSpeed=105 + Parallel Fallback
# -------------------------------------------------------------
PAIRS = [
    {"name": "Dallas -> Denver", "origin": (32.7767, -96.7970), "dest": (39.7392, -104.9903)},
    {"name": "Los Angeles -> Salt Lake City", "origin": (34.0522, -118.2437), "dest": (40.7608, -111.8910)},
    {"name": "Chicago -> Atlanta", "origin": (41.8781, -87.6298), "dest": (33.7490, -84.3880)},
    {"name": "Seattle -> Boise", "origin": (47.6062, -122.3321), "dest": (43.6150, -116.2023)},
]


def fetch_via_route(orig, via, dest, key, speed=105):
    url = f"{BASE_URL}/{orig[0]},{orig[1]}:{via[0]:.5f},{via[1]:.5f}:{dest[0]},{dest[1]}/json"
    p = {
        "key": key,
        "travelMode": "truck",
        "traffic": "false",
        "vehicleMaxSpeed": speed,
        "instructionsType": "tagged",
        "computeTravelTimeFor": "all",
    }
    with httpx.Client(timeout=25.0) as client:
        t0 = time.perf_counter()
        resp = client.get(url, params=p)
        wall = time.perf_counter() - t0
        return resp.json(), wall, (via[0], via[1])


def test_4_pairs_standard_and_fallback(client: httpx.Client, key: str):
    print("\n" + "=" * 70)
    print("2. 4 US PAIRS (traffic=false, vehicleMaxSpeed=105 km/h) & PARALLEL FALLBACK")
    print("=" * 70)

    summary_table = []

    for p in PAIRS:
        print(f"\n--- {p['name']} ---")
        orig, dest = p["origin"], p["dest"]
        url = f"{BASE_URL}/{orig[0]},{orig[1]}:{dest[0]},{dest[1]}/json"
        params = {
            "key": key,
            "travelMode": "truck",
            "traffic": "false",
            "vehicleMaxSpeed": 105,
            "maxAlternatives": 2,
            "instructionsType": "tagged",
            "computeTravelTimeFor": "all",
        }
        t0 = time.perf_counter()
        resp = client.get(url, params=params)
        call_time = time.perf_counter() - t0

        data = resp.json()
        native_routes = data.get("routes", [])
        print(f"Native routes returned: {len(native_routes)} (in {call_time:.2f}s)")

        routes_info = []
        native_polylines = []
        for idx, r in enumerate(native_routes):
            s = r["summary"]
            pts = [(pt["latitude"], pt["longitude"]) for leg in r["legs"] for pt in leg["points"]]
            native_polylines.append(pts)
            dist_mi = s["lengthInMeters"] * 0.000621371
            dur_s = s["travelTimeInSeconds"]
            dur_h = dur_s / 3600
            avg_spd = dist_mi / dur_h if dur_h > 0 else 0
            routes_info.append({
                "idx": idx + 1,
                "dist_mi": round(dist_mi, 1),
                "dur_s": dur_s,
                "dur_h": round(dur_h, 2),
                "avg_spd": round(avg_spd, 1),
                "pts_count": len(pts),
            })
            print(f"  Native Route #{idx+1}: {dist_mi:.1f} mi, {dur_h:.2f} h ({dur_s}s), avg {avg_spd:.1f} mph, {len(pts)} pts")

        fallback_info = None

        if len(native_routes) < 3:
            print(f"\n  Running §6 Fallback for {p['name']} (all 4 via requests in parallel)...")
            fastest_route = min(native_routes, key=lambda r: r["summary"]["travelTimeInSeconds"])
            fastest_pts = [(pt["latitude"], pt["longitude"]) for leg in fastest_route["legs"] for pt in leg["points"]]
            fastest_dist_mi = fastest_route["summary"]["lengthInMeters"] * 0.000621371
            fastest_dur_s = fastest_route["summary"]["travelTimeInSeconds"]

            cum_dist = polyline_cumulative_distances(fastest_pts)
            offset_dist = max(15.0, min(60.0, 0.12 * fastest_dist_mi))

            # Prepare 4 via points
            anchors = [0.33, 0.66]
            sides = [("33% Left (+90°)", 0.33, 90),
                     ("33% Right (-90°)", 0.33, -90),
                     ("66% Left (+90°)", 0.66, 90),
                     ("66% Right (-90°)", 0.66, -90)]

            via_configs = []
            for label, a_frac, angle in sides:
                anchor_pt, heading = point_at_fraction(fastest_pts, cum_dist, a_frac)
                perp_b = (heading + angle) % 360
                v_lat, v_lon = destination_point(anchor_pt[0], anchor_pt[1], perp_b, offset_dist)
                via_configs.append({"label": label, "via": (v_lat, v_lon)})

            # Fire in parallel with ThreadPoolExecutor
            wall_start = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(fetch_via_route, orig, cfg["via"], dest, key, 105): cfg
                    for cfg in via_configs
                }
                parallel_results = []
                for fut in concurrent.futures.as_completed(futures):
                    cfg = futures[fut]
                    res_json, req_wall, via_pt = fut.result()
                    parallel_results.append((cfg, res_json, req_wall))
            total_wall_time = time.perf_counter() - wall_start
            print(f"  All 4 parallel via requests completed in {total_wall_time:.2f}s wall time!")

            candidates = []
            for cfg, res_json, req_wall in parallel_results:
                r = res_json["routes"][0]
                s = r["summary"]
                d_mi = s["lengthInMeters"] * 0.000621371
                t_s = s["travelTimeInSeconds"]
                t_h = t_s / 3600
                d_ratio = t_s / fastest_dur_s
                c_pts = [(pt["latitude"], pt["longitude"]) for leg in r["legs"] for pt in leg["points"]]

                # Check overlap against all native routes
                overlaps = [compute_overlap_fraction(c_pts, nat_pts, threshold_mi=0.3) for nat_pts in native_polylines]
                max_ov = max(overlaps)
                is_qual = (max_ov < 0.85) and (d_ratio < 1.6)

                candidates.append({
                    "label": cfg["label"],
                    "dist_mi": round(d_mi, 1),
                    "dur_s": t_s,
                    "dur_h": round(t_h, 2),
                    "dur_ratio": round(d_ratio, 2),
                    "overlaps": [round(o * 100, 1) for o in overlaps],
                    "max_overlap_pct": round(max_ov * 100, 1),
                    "is_qualifying": is_qual,
                    "avg_spd": round(d_mi / t_h, 1),
                })
                print(f"    Candidate [{cfg['label']}]: {d_mi:.1f} mi, {t_h:.2f}h ({d_ratio:.2f}x fastest), max overlap {max_ov*100:.1f}% -> {'QUALIFIES' if is_qual else 'DISQUALIFIED'}")

            qualifying = [c for c in candidates if c["is_qualifying"]]
            best_candidate = min(qualifying, key=lambda c: c["max_overlap_pct"]) if qualifying else None

            fallback_info = {
                "total_wall_time_s": round(total_wall_time, 2),
                "candidates": candidates,
                "best_candidate": best_candidate
            }
            if best_candidate:
                print(f"  Lowest-overlap qualifying candidate: [{best_candidate['label']}] with {best_candidate['max_overlap_pct']}% overlap, {best_candidate['dist_mi']} mi, {best_candidate['dur_h']}h ({best_candidate['dur_ratio']}x)")

        summary_table.append({
            "pair": p["name"],
            "native_count": len(native_routes),
            "native_routes": routes_info,
            "fallback": fallback_info
        })

    return summary_table


# -------------------------------------------------------------
# 3. Via Route Instruction Continuity Across Legs Test
# -------------------------------------------------------------
def test_via_instruction_continuity(client: httpx.Client, key: str):
    print("\n" + "=" * 70)
    print("3. VIA ROUTE INSTRUCTION CONTINUITY & STITCHING TEST")
    print("=" * 70)

    # Dallas -> Lubbock (via) -> Denver
    orig = (32.7767, -96.7970)
    via = (33.5779, -101.8552)
    dest = (39.7392, -104.9903)

    url = f"{BASE_URL}/{orig[0]},{orig[1]}:{via[0]},{via[1]}:{dest[0]},{dest[1]}/json"
    params = {
        "key": key,
        "travelMode": "truck",
        "traffic": "false",
        "vehicleMaxSpeed": 105,
        "instructionsType": "tagged",
        "computeTravelTimeFor": "all",
    }
    resp = client.get(url, params=params)
    data = resp.json()
    route = data["routes"][0]
    summary = route["summary"]
    total_dist_m = summary["lengthInMeters"]
    total_dur_s = summary["travelTimeInSeconds"]
    legs = route.get("legs", [])
    guidance = route.get("guidance", {})
    instructions = guidance.get("instructions", [])

    print(f"Via Route: {summary['lengthInMeters'] * 0.000621371:.1f} mi, {total_dur_s/3600:.2f} h ({total_dur_s}s)")
    print(f"Number of legs: {len(legs)}")
    for l_idx, leg in enumerate(legs):
        ls = leg["summary"]
        print(f"  Leg #{l_idx+1}: {ls['lengthInMeters']*0.000621371:.1f} mi ({ls['lengthInMeters']}m), {ls['travelTimeInSeconds']/3600:.2f}h ({ls['travelTimeInSeconds']}s)")

    print(f"Total instructions in guidance: {len(instructions)}")

    # Check monotonicity and if reset occurs
    resets_detected = []
    is_monotonic_time = True
    is_monotonic_dist = True
    prev_t, prev_d = -1, -1

    for i, inst in enumerate(instructions):
        t = inst.get("travelTimeInSeconds", 0)
        d = inst.get("routeOffsetInMeters", 0)
        if t < prev_t:
            is_monotonic_time = False
            resets_detected.append({"index": i, "prev_t": prev_t, "curr_t": t, "prev_d": prev_d, "curr_d": d})
        if d < prev_d:
            is_monotonic_dist = False
        prev_t = t
        prev_d = d

    last_t = instructions[-1].get("travelTimeInSeconds", 0)
    last_d = instructions[-1].get("routeOffsetInMeters", 0)

    print(f"Monotonic non-decreasing across whole route? Time: {is_monotonic_time}, Dist: {is_monotonic_dist}")
    print(f"Resets detected: {len(resets_detected)}")
    if resets_detected:
        for r in resets_detected:
            print(f"  Reset at instruction #{r['index']}: time dropped from {r['prev_t']}s to {r['curr_t']}s, dist from {r['prev_d']}m to {r['curr_d']}m")

    print(f"Final instruction time: {last_t}s vs Summary travelTimeInSeconds: {total_dur_s}s (diff: {abs(total_dur_s - last_t)}s)")
    print(f"Final instruction offset: {last_d}m vs Summary lengthInMeters: {total_dist_m}m (diff: {abs(total_dist_m - last_d)}m)")

    return {
        "is_continuous": (len(resets_detected) == 0) and (last_t == total_dur_s),
        "resets": resets_detected,
        "last_t": last_t,
        "total_dur_s": total_dur_s,
        "last_d": last_d,
        "total_dist_m": total_dist_m
    }


def main():
    if not TOMTOM_KEY:
        print("[ERROR] TOMTOM_API_KEY is missing from environment.")
        sys.exit(1)

    with httpx.Client(timeout=30.0) as client:
        det_results = test_determinism(client, TOMTOM_KEY)
        std_results = test_4_pairs_standard_and_fallback(client, TOMTOM_KEY)
        via_results = test_via_instruction_continuity(client, TOMTOM_KEY)


if __name__ == "__main__":
    main()
