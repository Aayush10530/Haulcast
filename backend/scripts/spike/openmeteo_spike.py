"""
Open-Meteo spike script for Haulcast (F-000).
Tests multi-location batching, parameter compatibility, response shape, and latency.
No API key required.
"""

import json
import time
import httpx


def test_openmeteo():
    url = "https://api.open-meteo.com/v1/forecast"

    coords = [
        {"name": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
        {"name": "Denver, CO", "lat": 39.7392, "lon": -104.9903},
        {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
    ]

    lat_str = ",".join(str(c["lat"]) for c in coords)
    lon_str = ",".join(str(c["lon"]) for c in coords)

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

    print(f"Calling Open-Meteo with 3 coordinates...")
    start_time = time.perf_counter()
    with httpx.Client(timeout=15.0) as client:
        response = client.get(url, params=params)
    elapsed = time.perf_counter() - start_time

    print(f"HTTP Status: {response.status_code}")
    print(f"Elapsed Time: {elapsed:.3f} s")
    print(f"Response Body Size: {len(response.content)} bytes ({len(response.content) / 1024:.2f} KB)")

    if response.status_code != 200:
        print(f"Error response: {response.text}")
        return False

    data = response.json()

    # Verify if response is a list matching coords order
    if isinstance(data, list):
        print(f"\n[PASS] Response is a JSON list containing {len(data)} items matching request order.")
        items = data
    elif isinstance(data, dict):
        print(f"\n[NOTE] Single object returned. Checking structure...")
        items = [data]
    else:
        print(f"\n[FAIL] Unexpected response type: {type(data)}")
        return False

    for idx, item in enumerate(items):
        coord_req = coords[idx]
        tz_name = item.get("timezone")
        tz_abbrev = item.get("timezone_abbreviation")
        utc_offset = item.get("utc_offset_seconds")
        hourly = item.get("hourly", {})
        hourly_units = item.get("hourly_units", {})

        print(f"\nLocation #{idx+1} ({coord_req['name']}):")
        print(f"  Latitude: {item.get('latitude')}, Longitude: {item.get('longitude')}")
        print(f"  Timezone: {tz_name} ({tz_abbrev}), UTC offset: {utc_offset}s")
        print(f"  Units: {hourly_units}")

        # Check variables and time length
        times = hourly.get("time", [])
        wind = hourly.get("wind_speed_10m", [])
        rain = hourly.get("rain", [])
        showers = hourly.get("showers", [])
        snow = hourly.get("snowfall", [])

        print(f"  Hourly entries count: {len(times)}")
        print(f"  Expected approx: 3 past + 1 current + 288 forecast = ~292 hours")
        if times:
            print(f"  Time sample (first 3): {times[:3]}")
            print(f"  Time sample (last 3): {times[-3:]}")
            print(f"  Wind sample: {wind[:3]}")
            print(f"  Rain sample: {rain[:3]}")
            print(f"  Showers sample: {showers[:3]}")
            print(f"  Snowfall sample: {snow[:3]}")

        # Verify time format is unix epoch
        if times and isinstance(times[0], int):
            print(f"  [PASS] Timestamps are Unix epoch integers (e.g. {times[0]}).")
        else:
            print(f"  [WARN] Timestamps format: {type(times[0]) if times else 'empty'}")

    return True


if __name__ == "__main__":
    success = test_openmeteo()
    print(f"\nOpen-Meteo test overall: {'SUCCESS' if success else 'FAILED'}")
