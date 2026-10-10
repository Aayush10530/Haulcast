# Provider Spike Scripts (Phase P0 / F-000)

Throwaway evaluation scripts to verify routing, geocoding, and weather APIs before building production adapters.

## Contents

- `openmeteo_spike.py`: Tests Open-Meteo multi-coordinate requests, time offsets (`past_hours=3`, `forecast_hours=288`), hourly parameters (`wind_speed_10m`, `rain`, `showers`, `snowfall`), units (`mph`, `inch`, `unixtime`), and IANA timezone resolution. Requires no API key.
- `openmeteo_batch_spike.py`: Tests Open-Meteo batch scaling at 50 and 100 locations in 1 HTTP call.
- `tomtom_spike.py`: Tests TomTom Routing API with truck mode, alternatives, fallback via-waypoints, timeline instructions, and typeahead search. Requires `TOMTOM_API_KEY`.

## Usage

```bash
# Open-Meteo (no key needed)
python backend/scripts/spike/openmeteo_spike.py
python backend/scripts/spike/openmeteo_batch_spike.py

# TomTom (requires key in backend/.env)
python backend/scripts/spike/tomtom_spike.py
```
