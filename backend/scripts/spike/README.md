# Provider Spike Evaluation (Phase P0 / F-000 / F-065)

This directory contains the Phase P0 provider evaluation harness used to verify routing, geocoding, and weather APIs before building production adapters.

## Consolidated Script

All provider evaluations are consolidated into `provider_spike.py`:

- **Open-Meteo Weather Evaluation**:
  - Validates multi-coordinate batch requests (`past_hours=3`, `forecast_hours=288`).
  - Verifies parameters (`wind_speed_10m`, `rain`, `showers`, `snowfall`), unit formatting (`mph`, `inch`, `unixtime`), and IANA timezone name resolution.
  - Stress tests batch scaling at 50 and 100 locations in a single HTTP call.
  - Requires no API key.
- **TomTom Commercial Truck Routing & Geocoding Evaluation**:
  - Tests commercial truck mode (`travelMode=truck`, `vehicleMaxSpeed=105` governor limit).
  - Verifies instruction timeline monotonicity and cumulative ETA alignment.
  - Tests 4 long US transcontinental pairs (Dallas $\rightarrow$ Denver, LA $\rightarrow$ Salt Lake City, Chicago $\rightarrow$ Atlanta, Seattle $\rightarrow$ Boise).
  - Tests via-waypoint diversification fallback and geocoding typeahead search (`countrySet=US`).
  - Requires `TOMTOM_API_KEY` in `backend/.env`.

## Usage

```bash
# Run weather evaluations only (no API key required)
python backend/scripts/spike/provider_spike.py --weather

# Run TomTom routing & geocoding evaluations only (requires TOMTOM_API_KEY)
python backend/scripts/spike/provider_spike.py --routing

# Run full evaluation suite
python backend/scripts/spike/provider_spike.py --all
```
