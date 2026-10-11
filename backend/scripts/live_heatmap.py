"""Live script testing /api/trips/heatmap/ endpoint against running server.

Prints cell count, frame count, raw and gzip response size, cold and warm times for a Dallas -> Denver trip.
"""

import datetime
import gzip
import os
from pathlib import Path
import sys
import time

import httpx

# Ensure backend directory is in path and env is loaded
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

env_path = backend_dir / ".env"
if env_path.exists():
    try:
        import dotenv

        dotenv.load_dotenv(env_path)
    except ImportError:
        pass


def run_heatmap_request(client: httpx.Client, url: str) -> dict:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    departure_local = f"{tomorrow.isoformat()}T08:00"

    payload = {
        "origin": {"label": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
        "destination": {"label": "Denver, CO", "lat": 39.7392, "lon": -104.9903},
        "departure_local": departure_local,
        "load_weight_lb": 42000,
    }

    t0 = time.perf_counter()
    resp = client.post(url, json=payload, timeout=60.0)
    elapsed_wall = time.perf_counter() - t0

    content_bytes = resp.content
    gzip_bytes = gzip.compress(content_bytes)

    data = None
    if resp.status_code == 200:
        data = resp.json()

    return {
        "status": resp.status_code,
        "elapsed_wall": elapsed_wall,
        "raw_size_bytes": len(content_bytes),
        "gzip_size_bytes": len(gzip_bytes),
        "data": data if data is not None else resp.text,
    }


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    url = f"http://127.0.0.1:{port}/api/trips/heatmap/"

    print("==================================================")
    print("Haulcast Live Heatmap Test: Dallas, TX -> Denver, CO")
    print(f"Target URL: {url}")
    print("==================================================")

    with httpx.Client() as client:
        # 1. Cold Run
        print("\nExecuting Cold Run...")
        cold_result = run_heatmap_request(client, url)

        # 2. Warm Run
        print("Executing Warm Run...")
        warm_result = run_heatmap_request(client, url)

    if cold_result["status"] != 200:
        print(f"\nCold run failed with status {cold_result['status']}:")
        print(cold_result["data"])
        return

    data = cold_result["data"]
    cells = data.get("cells", [])
    frames = data.get("frames", [])

    print("\n--- Heatmap Results ---")
    print(f"Cell Count:          {len(cells)}")
    print(f"Frame Count:         {len(frames)}")
    print(f"Raw Response Size:   {cold_result['raw_size_bytes']:,} bytes ({cold_result['raw_size_bytes'] / 1024:.1f} KB)")
    print(f"Gzip Response Size:  {cold_result['gzip_size_bytes']:,} bytes ({cold_result['gzip_size_bytes'] / 1024:.1f} KB)")
    print(f"Cold Elapsed Time:   {cold_result['elapsed_wall']:.2f}s")
    print(f"Warm Elapsed Time:   {warm_result['elapsed_wall']:.2f}s")
    print("-----------------------")


if __name__ == "__main__":
    main()
