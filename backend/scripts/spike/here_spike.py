"""
HERE Routing and Geocoding spike script for Haulcast (F-000).
Requires HERE_API_KEY in environment or .env.
Tests 4 US pairs with truck transportMode, alternatives, polyline, and autocomplete.
"""

import os
import sys
import time
from pathlib import Path
import httpx

# Automatically load backend/.env if present
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

HERE_KEY = os.environ.get("HERE_API_KEY")

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


def test_here_routing(client: httpx.Client, key: str):
    print("=" * 60)
    print("1. HERE ROUTING V8 TESTS (4 US PAIRS)")
    print("=" * 60)

    url = "https://router.hereapi.com/v8/routes"

    for pair in PAIRS:
        origin_str = f"{pair['origin'][0]},{pair['origin'][1]}"
        dest_str = f"{pair['destination'][0]},{pair['destination'][1]}"

        params = {
            "apiKey": key,
            "origin": origin_str,
            "destination": dest_str,
            "transportMode": "truck",
            "alternatives": 2,
            "return": "polyline,summary,actions,instructions",
        }

        print(f"\nRequesting: {pair['name']} (truck mode, alternatives=2)...")
        start = time.perf_counter()
        resp = client.get(url, params=params)
        elapsed = time.perf_counter() - start

        print(f"  Status: {resp.status_code} | Time: {elapsed:.2f}s | Size: {len(resp.content)/1024:.1f} KB")

        if resp.status_code != 200:
            print(f"  [ERROR] {resp.text[:300]}")
            continue

        data = resp.json()
        routes = data.get("routes", [])
        print(f"  Routes returned: {len(routes)}")

        for idx, r in enumerate(routes):
            sections = r.get("sections", [])
            total_meters = sum(s.get("summary", {}).get("length", 0) for s in sections)
            total_duration = sum(s.get("summary", {}).get("duration", 0) for s in sections)
            dist_miles = total_meters * 0.000621371
            hours = total_duration / 3600

            print(
                f"    Route #{idx+1}: {dist_miles:.1f} mi, {hours:.2f} hrs ({total_duration}s), "
                f"sections: {len(sections)}"
            )


def test_here_geocoding(client: httpx.Client, key: str):
    print("\n" + "=" * 60)
    print("2. HERE GEOCODING / AUTOCOMPLETE TEST")
    print("=" * 60)

    url = "https://autocomplete.search.hereapi.com/v1/autocomplete"

    queries = ["dalla", "denv"]
    for q in queries:
        params = {
            "apiKey": key,
            "q": q,
            "limit": 5,
            "in": "countryCode:USA",
        }

        start = time.perf_counter()
        resp = client.get(url, params=params)
        elapsed = time.perf_counter() - start

        print(f"\nQuery '{q}': status {resp.status_code} ({elapsed:.2f}s)")
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            print(f"  Items found: {len(items)}")
            for idx, item in enumerate(items[:3]):
                title = item.get("title", "N/A")
                print(f"    #{idx+1}: {title}")
        else:
            print(f"  [FAIL] {resp.text[:200]}")


def main():
    if not HERE_KEY:
        print("[ERROR] HERE_API_KEY environment variable is not set.")
        print("Please set HERE_API_KEY to run the HERE spike.")
        sys.exit(1)

    with httpx.Client(timeout=15.0) as client:
        test_here_routing(client, HERE_KEY)
        test_here_geocoding(client, HERE_KEY)


if __name__ == "__main__":
    main()
