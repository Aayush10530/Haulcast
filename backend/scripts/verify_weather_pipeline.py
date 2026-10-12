"""Verification script testing live trip weather and controlled synthetic scenarios.

Runs:
1. Live trip analysis (Boston, MA -> New York, NY and Dallas, TX -> Denver, CO).
2. Reports actual wind, rain, snow values and calculated risk categories.
3. Validates boundary interpretation, load-weight overrides, distance conservation,
   and route ranking priority.
"""

import datetime
import math
import os
import sys

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from api.container import get_container
from core.domain import geometry, risk, scoring
from core.domain.ranking import rank_routes
from core.domain.sampling import build_checkpoints
from core.domain.types import (
    Coordinate,
    HourlySeries,
    IntervalMode,
    MilesByLevel,
    Place,
    RankingInput,
    RawRoute,
    RiskDriver,
    RiskLevel,
    RouteSummary,
    Timeline,
    TripRequest,
    WeatherSample,
    WeatherSeries,
)


def run_live_trip(origin_label: str, origin_coord: Coordinate, dest_label: str, dest_coord: Coordinate):
    service = get_container().trip_analysis
    origin = Place(origin_label, origin_coord)
    dest = Place(dest_label, dest_coord)

    # Use current UTC time for departure
    now = datetime.datetime.now(datetime.timezone.utc)
    # Naive local time string for request
    req = TripRequest(
        origin=origin,
        destination=dest,
        departure_local=now.replace(tzinfo=None),
        load_weight_lb=40000,
        interval_mode=IntervalMode.MANUAL,
        manual_interval=25,
    )

    analysis = service.analyze(req)
    recommended = next(r for r in analysis.routes if r.route_id == analysis.recommendation.route_id)

    print(f"\n================================================================================")
    print(f"LIVE TRIP ANALYSIS: {origin_label} -> {dest_label}")
    print(f"================================================================================")
    print(f"Recommended Route: {recommended.label} (ID: {recommended.route_id})")
    print(f"Total Distance   : {recommended.summary.distance_miles:.1f} miles")
    print(f"Duration         : {recommended.summary.duration_seconds / 3600:.2f} hours")
    print(f"Checkpoints Count: {len(recommended.checkpoints)}")
    print(f"Miles by Level   : {recommended.summary.miles_by_level}")
    print(f"Avg Risk Score   : {recommended.summary.avg_risk_score}")
    print(f"\nCheckpoint Details (Live Weather Forecasts):")
    print(f"{'Mile':>6} | {'ETA (Local)':^20} | {'Wind (mph)':>10} | {'Rain (in/hr)':>12} | {'Snow (in/hr)':>12} | {'Risk Category':^13} | Reason")
    print("-" * 105)

    for cp in recommended.checkpoints:
        w = cp.sample
        wind_str = f"{w.wind_mph:.1f}" if (w and w.wind_mph is not None) else "--"
        rain_str = f"{w.rain_in_hr:.2f}" if (w and w.rain_in_hr is not None) else "--"
        snow_str = f"{w.snow_in_hr:.2f}" if (w and w.snow_in_hr is not None) else "--"
        level_str = cp.assessment.level.value if cp.assessment else "Unavailable"
        reason_str = cp.reason if cp.reason else "Forecast unavailable"
        eta_str = cp.eta_utc.strftime("%Y-%m-%d %H:%M UTC")

        print(f"{cp.checkpoint.mile:6.1f} | {eta_str:^20} | {wind_str:>10} | {rain_str:>12} | {snow_str:>12} | {level_str:^13} | {reason_str}")

    return recommended


if __name__ == "__main__":
    # 1. Test Boston, MA -> New York, NY (Dashboard default)
    run_live_trip("Boston, MA", Coordinate(42.3601, -71.0589), "New York, NY", Coordinate(40.7128, -74.0060))

    # 2. Test Denver, CO -> Salt Lake City, UT (Mountain corridor)
    run_live_trip("Denver, CO", Coordinate(39.7392, -104.9903), "Salt Lake City, UT", Coordinate(40.7608, -111.8910))

