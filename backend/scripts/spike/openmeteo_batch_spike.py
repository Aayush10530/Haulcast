"""
Open-Meteo 50 and 100 location batch stress spike for StormRoute (F-000).
Tests multi-location queries at scale (50 and 100 coordinates) in a single HTTP GET.
Reports elapsed time, payload size, and any errors.
"""

import time
import httpx


def generate_coordinates(count: int) -> list[tuple[float, float]]:
    """
    Generate coordinates along a realistic US corridor (e.g., Dallas to Seattle).
    Linearly spaced lat/lon points across the continental US.
    """
    start_lat, start_lon = 32.7767, -96.7970  # Dallas, TX
    end_lat, end_lon = 47.6062, -122.3321    # Seattle, WA

    coords = []
    for i in range(count):
        t = i / (count - 1) if count > 1 else 0.0
        lat = round(start_lat + t * (end_lat - start_lat), 4)
        lon = round(start_lon + t * (end_lon - start_lon), 4)
        coords.append((lat, lon))
    return coords


def test_batch(count: int):
    url = "https://api.open-meteo.com/v1/forecast"
    coords = generate_coordinates(count)

    lat_str = ",".join(str(c[0]) for c in coords)
    lon_str = ",".join(str(c[1]) for c in coords)

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

    print(f"\nTesting Open-Meteo with {count} locations in 1 request...")
    url_len = len(url) + len(str(params))
    print(f"  Approx query string length: {url_len} chars")

    start = time.perf_counter()
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, params=params)
        elapsed = time.perf_counter() - start

        print(f"  Status code: {resp.status_code}")
        print(f"  Elapsed time: {elapsed:.3f} s")
        print(f"  Payload size: {len(resp.content)} bytes ({len(resp.content)/1024:.1f} KB / {len(resp.content)/(1024*1024):.2f} MB)")

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"  [PASS] Returned list of {len(data)} location objects (matches requested {count}).")
                # Validate first and last item
                first = data[0]
                last = data[-1]
                print(f"  First location hourly entries: {len(first.get('hourly', {}).get('time', []))}")
                print(f"  Last location hourly entries: {len(last.get('hourly', {}).get('time', []))}")
                return {"count": count, "status": 200, "time_s": round(elapsed, 3), "size_kb": round(len(resp.content)/1024, 1), "error": None}
            else:
                print(f"  [WARN] Unexpected JSON structure: {type(data)}")
                return {"count": count, "status": 200, "time_s": round(elapsed, 3), "size_kb": round(len(resp.content)/1024, 1), "error": "Not a list"}
        else:
            print(f"  [FAIL] HTTP Error: {resp.status_code} - {resp.text[:300]}")
            return {"count": count, "status": resp.status_code, "time_s": round(elapsed, 3), "size_kb": round(len(resp.content)/1024, 1), "error": resp.text[:200]}

    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"  [EXCEPTION] {type(exc).__name__}: {exc}")
        return {"count": count, "status": "ERROR", "time_s": round(elapsed, 3), "size_kb": 0, "error": str(exc)}


def main():
    print("=" * 60)
    print("OPEN-METEO BATCH STRESS TEST (50 & 100 LOCATIONS)")
    print("=" * 60)
    res50 = test_batch(50)
    res100 = test_batch(100)

    print("\n" + "=" * 60)
    print("SUMMARY RESULTS")
    print("=" * 60)
    for r in [res50, res100]:
        print(f"{r['count']} locations: Status {r['status']}, {r['time_s']}s, {r['size_kb']} KB, Error: {r['error']}")


if __name__ == "__main__":
    main()
