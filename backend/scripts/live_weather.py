"""Live script testing Open-Meteo weather adapter and cache (F-023)."""

from pathlib import Path
import os
import sys
import time

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from core.domain.grid import snap_to_cell
from core.domain.types import Coordinate, GridCell
from core.infra.cache import DjangoCache
from core.providers.weather_openmeteo import OpenMeteoWeatherProvider


def main() -> None:
    cache = DjangoCache()
    provider = OpenMeteoWeatherProvider(cache=cache)

    # 1. Three cells: Dallas, Denver, Chicago
    dallas = Coordinate(lat=32.7767, lon=-96.7970)
    denver = Coordinate(lat=39.7392, lon=-104.9903)
    chicago = Coordinate(lat=41.8781, lon=-87.6298)

    cell_dallas = snap_to_cell(dallas)
    cell_denver = snap_to_cell(denver)
    cell_chicago = snap_to_cell(chicago)
    three_cells = [cell_dallas, cell_denver, cell_chicago]

    print("=== STEP 1: Fetching 3 cells (Dallas, Denver, Chicago) ===")
    t0 = time.perf_counter()
    series_map = provider.get_series(three_cells)
    elapsed_3 = time.perf_counter() - t0

    for name, cell in [
        ("Dallas", cell_dallas),
        ("Denver", cell_denver),
        ("Chicago", cell_chicago),
    ]:
        s = series_map[cell]
        hourly_count = len(s.wind_mph.values)
        first_wind = s.wind_mph.values[0]
        print(
            f"  {name} ({cell.lat_index}, {cell.lon_index}): "
            f"tz={s.tz_name}, hourly_entries={hourly_count}, "
            f"first_wind={first_wind} mph"
        )
    print(f"3 cells elapsed time: {elapsed_3:.3f}s\n")

    # 2. 100 cells
    print("=== STEP 2: Fetching 100 cells (Single chunk) ===")
    hundred_cells: list[GridCell] = [
        snap_to_cell(Coordinate(lat=30.0 + i * 0.1, lon=-95.0))
        for i in range(100)
    ]

    t1 = time.perf_counter()
    res_100 = provider.get_series(hundred_cells)
    elapsed_100 = time.perf_counter() - t1
    print(f"100 cells fetched: {len(res_100)} items in {elapsed_100:.3f}s\n")

    # 3. Same 100 cells again (must be instant from cache)
    print("=== STEP 3: Re-fetching the same 100 cells (Cache hit) ===")
    t2 = time.perf_counter()
    res_cached = provider.get_series(hundred_cells)
    elapsed_cached = time.perf_counter() - t2
    print(f"100 cells cache hit: {len(res_cached)} items in {elapsed_cached:.4f}s")
    assert len(res_cached) == 100
    print("\nLive weather test completed successfully.")


if __name__ == "__main__":
    main()
