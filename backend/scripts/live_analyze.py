"""Live script testing /api/trips/analyze/ endpoint against running server."""

import datetime
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


def run_analyze_request(client: httpx.Client, url: str) -> dict:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    departure_local = f"{tomorrow.isoformat()}T08:00"

    payload = {
        "origin": {"label": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
        "destination": {"label": "Denver, CO", "lat": 39.7392, "lon": -104.9903},
        "departure_local": departure_local,
        "load_weight_lb": 42000,
        "interval": "auto",
    }

    t0 = time.perf_counter()
    resp = client.post(url, json=payload, timeout=35.0)
    elapsed_wall = time.perf_counter() - t0

    return {
        "status": resp.status_code,
        "elapsed_wall": elapsed_wall,
        "data": resp.json() if resp.status_code == 200 else resp.text,
    }


def print_run_results(run_label: str, result: dict) -> None:
    print(f"\n=== {run_label} RUN ===")
    print(f"HTTP Status: {result['status']}")
    print(f"Total Wall Time: {result['elapsed_wall']:.2f}s")

    if result["status"] != 200:
        print(f"Error Response: {result['data']}")
        return

    data = result["data"]
    meta = data.get("meta", {})
    routes = data.get("routes", [])

    routing_sec = meta.get("routing_ms", 0.0) / 1000.0
    weather_sec = meta.get("weather_ms", 0.0) / 1000.0
    in_process_sec = meta.get("in_process_ms", 0.0) / 1000.0
    unique_cells = meta.get("weather_cells", 0)

    print(
        f"Time Breakdown: Routing Call = {routing_sec:.2f}s, "
        f"Weather Call = {weather_sec:.2f}s, "
        f"In-Process Work = {in_process_sec:.2f}s"
    )
    print(f"Unique Weather Cells: {unique_cells}")
    cp_counts = [
        f"{r.get('label')} ({r.get('id')}): {len(r.get('checkpoints', []))}" for r in routes
    ]
    print(f"Checkpoints Per Route: {', '.join(cp_counts)}")
    print(f"Number of Routes: {len(routes)}")

    for r in routes:
        summ = r.get("summary", {})
        m_level = summ.get("miles_by_level", {})
        duration_hrs = r.get("duration_seconds", 0) / 3600.0
        print(
            f"  [{r.get('id')}] {r.get('label')}: "
            f"distance={r.get('distance_miles')} mi, "
            f"duration={r.get('duration_seconds')}s ({duration_hrs:.2f}h), "
            f"severe={m_level.get('severe', 0.0)} mi, "
            f"high={m_level.get('high', 0.0)} mi, "
            f"avg_risk={summ.get('avg_risk_score')}"
        )

    rec = data.get("recommendation", {})
    print(f"Recommended Route: {rec.get('route_id')}")
    print(f"Headline: {rec.get('headline')}")
    print(f"Warnings: {data.get('warnings', [])}")
    print(f"Meta: {meta}")

    if run_label == "COLD" and result["elapsed_wall"] > 6.0:
        timings = [
            ("Routing Call", routing_sec),
            ("Weather Call", weather_sec),
            ("In-Process Work", in_process_sec),
        ]
        slowest_name, slowest_time = max(timings, key=lambda t: t[1])
        print("\n[SLOW RUN DETECTED > 6s]")
        print(f"Slowest step: {slowest_name} ({slowest_time:.2f}s)")
        if slowest_name == "Routing Call":
            print(
                "Proposed fix: Query route alternatives concurrently or parallelize via-point queries."
            )
        elif slowest_name == "Weather Call":
            print(
                "Proposed fix: Fetch Open-Meteo chunks in parallel using httpx.AsyncClient or asyncio.gather."
            )
        else:
            print("Proposed fix: Optimize polyline sampling or checkpoint timeline interpolation.")


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    url = f"http://127.0.0.1:{port}/api/trips/analyze/"

    with httpx.Client() as client:
        # Run 1: Cold run
        res_cold = run_analyze_request(client, url)
        print_run_results("COLD", res_cold)

        # Run 2: Warm run
        res_warm = run_analyze_request(client, url)
        print_run_results("WARM", res_warm)


if __name__ == "__main__":
    main()
